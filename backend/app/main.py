from contextlib import asynccontextmanager
import os
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from sqlalchemy import text

from app.config import Settings, get_settings
from app.errors import ApiError, handle_api_error, handle_unexpected_error, handle_validation_error
from app.api.projects import router as projects_router
from app.api.design import router as design_router
from app.api.runs import router as runs_router
from app.api.builds import router as builds_router
from app.api.candidates import router as candidates_router
from app.api.playables import router as playables_router
from app.api.releases import router as releases_router
from app.agents.fake_game_agent import FakeGameAgent
from app.agents.fake_game_design_planner import FakeGameDesignPlanner
from app.agents.fake_candidate_test_runner import FakeCandidateTestRunner
from app.agents.openai_game_design_planner import OpenAICompatibleGameDesignPlanner
from app.agents.opengame_adapter import OpenGameAdapter
from app.agents.subprocess_executor import AsyncSubprocessExecutor
from app.services.builds import BuildService
from app.services.project_git import ProjectGitService
from sqlalchemy.orm import Session
from app.db import create_engine_for


SERVICE_NAME = "ai-cowork-game-api"
APPLICATION_VERSION = "0.1.0"


def create_app(
    settings: Settings | None = None,
    *,
    game_agent=None,
    candidate_test_runner=None,
    game_design_planner=None,
) -> FastAPI:
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        with Session(application.state.engine) as session:
            recovered = BuildService(session, application.state.game_agent).recover_orphaned_jobs()
            if recovered:
                session.commit()
        yield

    app = FastAPI(title="AI Cowork Game API", version=APPLICATION_VERSION, lifespan=lifespan)
    app.state.settings = settings
    app.state.engine = create_engine_for(settings)
    # Keep the trusted Project Git root injectable for isolated API tests while
    # production uses the same deterministic default as C20 checkpoints.
    app.state.project_git = ProjectGitService()
    if game_design_planner is not None:
        app.state.game_design_planner = game_design_planner
    elif settings.game_design_provider == "fake":
        app.state.game_design_planner = FakeGameDesignPlanner()
    elif settings.game_design_provider == "openai":
        app.state.game_design_planner = OpenAICompatibleGameDesignPlanner(
            base_url=os.environ.get("OPENAI_BASE_URL"),
            api_key=os.environ.get("OPENAI_API_KEY"),
            model=settings.game_design_model,
            timeout_seconds=settings.game_design_timeout_seconds,
        )
    elif settings.game_design_provider == "none":
        app.state.game_design_planner = None
    else:
        raise ValueError(f"unsupported GAME_DESIGN_PROVIDER: {settings.game_design_provider}")
    if game_agent is not None:
        app.state.game_agent = game_agent
    elif settings.game_agent_provider == "fake":
        app.state.game_agent = FakeGameAgent()
    elif settings.game_agent_provider == "opengame":
        app.state.game_agent = OpenGameAdapter(
            AsyncSubprocessExecutor(),
            model=settings.opengame_model,
            openai_api_key=os.environ.get("OPENAI_API_KEY"),
            openai_base_url=os.environ.get("OPENAI_BASE_URL"),
            timeout_seconds=settings.opengame_timeout_seconds,
            opengame_cli_js=settings.opengame_cli_js,
            require_credentials=True,
        )
    else:
        raise ValueError(f"unsupported GAME_AGENT_PROVIDER: {settings.game_agent_provider}")
    app.state.candidate_test_provider = settings.candidate_test_provider
    app.state.candidate_test_runner = candidate_test_runner
    if candidate_test_runner is None and settings.candidate_test_provider == "fake":
        app.state.candidate_test_runner = FakeCandidateTestRunner("pass")
    app.add_exception_handler(ApiError, handle_api_error)
    app.add_exception_handler(RequestValidationError, handle_validation_error)
    app.add_exception_handler(Exception, handle_unexpected_error)
    app.include_router(projects_router)
    app.include_router(design_router)
    app.include_router(runs_router)
    app.include_router(builds_router)
    app.include_router(candidates_router)
    app.include_router(playables_router)
    app.include_router(releases_router)

    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        request.state.request_id = request.headers.get("X-Request-ID", str(uuid4()))
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        return response

    @app.get("/healthz")
    def healthz(request: Request) -> dict[str, str]:
        try:
            with request.app.state.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
        except Exception as cause:
            raise ApiError("dependency_unavailable", "Database unavailable", [], 503) from cause
        return {
            "status": "ok",
            "service": SERVICE_NAME,
            "version": APPLICATION_VERSION,
        }

    return app


app = create_app()
