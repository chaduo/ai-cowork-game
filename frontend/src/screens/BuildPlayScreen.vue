<script setup lang="ts">
import { ref } from 'vue'
import {
  BadgeCheck,
  Blocks,
  Bot,
  Boxes,
  Braces,
  ChevronDown,
  CircleHelp,
  Code2,
  FileText,
  Fish,
  FlaskConical,
  FolderKanban,
  Fullscreen,
  Gamepad2,
  History,
  Image,
  Info,
  Maximize2,
  MessageSquareText,
  MoreHorizontal,
  RefreshCw,
  RotateCcw,
  Send,
  Settings2,
  ShieldCheck,
  SlidersHorizontal,
  Volume2,
} from 'lucide-vue-next'

const request = ref('机器人太快了，速度降低 20%，再给猫增加一个冲刺技能。')
const submitted = ref(false)

function submitModification() {
  submitted.value = true
  window.setTimeout(() => {
    submitted.value = false
  }, 1800)
}
</script>

<template>
  <div class="app-shell">
    <header class="topbar">
      <div class="brand" aria-label="AI Cowork Game">
        <span class="brand-mark"><Gamepad2 :size="18" stroke-width="1.8" /></span>
        <span class="brand-name">AI Cowork Game</span>
      </div>

      <button class="project-switcher" type="button">
        <span class="project-label">当前项目</span>
        <strong>Kitchen Cat Survival</strong>
        <span class="project-state">Active</span>
        <ChevronDown :size="15" />
      </button>

      <div class="topbar-actions">
        <span class="runtime-label"><span class="runtime-dot"></span>Mock runtime</span>
        <button class="icon-button top-icon" type="button" title="帮助" aria-label="帮助">
          <CircleHelp :size="17" />
        </button>
        <button class="top-action" type="button"><RotateCcw :size="15" />重置演示</button>
      </div>
    </header>

    <aside class="navigation" aria-label="项目导航">
      <div class="nav-project">
        <span class="nav-project-icon"><FolderKanban :size="17" /></span>
        <div>
          <strong>橘猫厨房夜班</strong>
          <span>Phaser 2D · Active</span>
        </div>
      </div>

      <nav class="nav-list">
        <p class="nav-section-label">PROJECT</p>
        <a href="#"><Blocks :size="17" />项目概览</a>
        <div class="nav-group">
          <div class="nav-group-label"><FileText :size="17" />设计</div>
          <a class="nav-child" href="#"><span>GDD</span><BadgeCheck :size="14" class="approved-icon" /></a>
          <a class="nav-child" href="#"><span>GameSpec</span><BadgeCheck :size="14" class="approved-icon" /></a>
        </div>
        <a href="#"><Image :size="17" />素材<span class="nav-count">5</span></a>
        <a class="active" href="#"><Gamepad2 :size="17" />构建与试玩</a>
        <a href="#"><Code2 :size="17" />代码</a>
        <a href="#"><History :size="17" />版本</a>

        <p class="nav-section-label resources-label">PLATFORM</p>
        <a href="#"><Boxes :size="17" />可复用资源</a>
      </nav>

      <div class="nav-foot">
        <ShieldCheck :size="16" />
        <span><strong>隔离工作区</strong>本项目文件已受保护</span>
      </div>
    </aside>

    <main class="workspace">
      <section class="workspace-header">
        <div class="artifact-identity">
          <span class="artifact-kicker">BUILD &amp; PLAY</span>
          <div class="artifact-title-row">
            <h1>构建与试玩</h1>
            <span class="artifact-id">artifact / playable-v2</span>
          </div>
        </div>

        <div class="dual-track" aria-label="Playable 和 Candidate 状态">
          <div class="track track-playable">
            <div class="track-label"><BadgeCheck :size="15" />PLAYABLE</div>
            <strong class="track-version">V2</strong>
            <span class="track-status">PASS</span>
            <span class="track-copy">已验证</span>
            <span class="track-line"><i></i></span>
            <span class="track-time">14:32</span>
            <button type="button">打开试玩</button>
          </div>
          <div class="track track-candidate">
            <div class="track-label"><FlaskConical :size="14" />CANDIDATE</div>
            <span class="candidate-empty">No active candidate</span>
            <span class="track-line empty"><i></i></span>
            <span class="candidate-hint">修改后将在这里运行</span>
          </div>
        </div>
      </section>

      <section class="main-workspace">
        <div class="preview-workbench">
          <div class="preview-toolbar">
            <div class="preview-source">
              <span class="live-dot"></span>
              <strong>V2 Playable</strong>
              <span>production build</span>
            </div>
            <div class="preview-controls" aria-label="预览控制">
              <button class="icon-button" type="button" title="重新载入" aria-label="重新载入"><RefreshCw :size="16" /></button>
              <button class="icon-button" type="button" title="声音" aria-label="声音"><Volume2 :size="16" /></button>
              <button class="icon-button" type="button" title="全屏" aria-label="全屏"><Fullscreen :size="16" /></button>
              <button class="open-preview" type="button"><Maximize2 :size="15" />新窗口试玩</button>
            </div>
          </div>

          <div class="game-frame">
            <img src="/game-preview.png" alt="橙猫在厨房躲避扫地机器人、收集鱼并与 NPC 互动的俯视角游戏画面" />
            <div class="game-hud hud-top-left">
              <span class="heart">♥</span><strong>100</strong>
              <span class="hud-divider"></span>
              <Fish :size="15" /><strong>06</strong>
            </div>
            <div class="game-hud hud-top-right"><strong>02:18</strong><span>SCORE 1240</span></div>
            <div class="npc-prompt"><MessageSquareText :size="14" /> E · 与米拉交谈</div>
            <div class="game-controls-hint"><span>WASD</span> 移动 <span>SPACE</span> 攻击</div>
          </div>

          <div class="preview-evidence">
            <div><span>构建</span><strong><BadgeCheck :size="14" />PASS</strong></div>
            <div><span>可玩性检查</span><strong><BadgeCheck :size="14" />8 / 8</strong></div>
            <div><span>产物</span><code>dist/v2 · 8f42a1</code></div>
            <button type="button"><FileText :size="14" />查看 TestReport</button>
          </div>
        </div>

        <aside class="context-panel">
          <div class="context-heading">
            <div>
              <span class="context-kicker"><Bot :size="14" />AI COWORK</span>
              <h2>AI 修改游戏</h2>
            </div>
            <button class="icon-button" type="button" title="更多选项" aria-label="更多选项"><MoreHorizontal :size="18" /></button>
          </div>

          <p class="context-intro">描述要改变的规则或体验。AI 将基于 V2 创建新的 Candidate，不会覆盖当前可玩版本。</p>

          <form class="modify-form" @submit.prevent="submitModification">
            <label for="modify-request">修改要求</label>
            <textarea id="modify-request" v-model="request" rows="5"></textarea>
            <div class="composer-meta">
              <span><Braces :size="13" />增量修改</span>
              <span>{{ request.length }} / 500</span>
            </div>
            <button class="primary-action" type="submit" :disabled="submitted || !request.trim()">
              <Send v-if="!submitted" :size="16" />
              <RefreshCw v-else :size="16" class="spin" />
              {{ submitted ? '正在创建 Candidate…' : '让 AI 修改' }}
            </button>
          </form>

          <div class="context-section">
            <div class="section-heading"><h3>当前上下文</h3><span>from V2</span></div>

            <div class="context-record">
              <div class="record-icon"><SlidersHorizontal :size="16" /></div>
              <div>
                <span class="record-label">当前规则</span>
                <strong>厨房生存 · 3:00</strong>
                <p>扫地机器人速度 86 · 猫咪生命 100 · 冲刺未启用</p>
              </div>
            </div>

            <div class="context-record">
              <div class="record-icon"><MessageSquareText :size="16" /></div>
              <div>
                <span class="record-label">当前 NPC</span>
                <strong>米拉 · 厨房向导</strong>
                <p>巡逻行为 · 近距离触发 2 段对话</p>
              </div>
            </div>

            <div class="context-record playable-record">
              <div class="record-icon"><BadgeCheck :size="16" /></div>
              <div>
                <span class="record-label">当前可玩版本</span>
                <strong>V2 · PASS</strong>
                <p>8 项可玩性检查通过 · 14:32 发布</p>
              </div>
            </div>
          </div>

          <div class="human-gates">
            <span><BadgeCheck :size="14" />GDD 已确认</span>
            <span><BadgeCheck :size="14" />GameSpec 已确认</span>
          </div>

          <div v-if="submitted" class="local-toast" role="status">
            <Info :size="15" />已提交 Mock 修改；V2 仍保持可玩
          </div>
        </aside>
      </section>
    </main>

    <footer class="status-footer">
      <span><span class="footer-dot"></span>视觉原型 · Mock data</span>
      <span>Desktop 1440 × 900</span>
      <span class="footer-right"><Settings2 :size="13" />workspace isolated <code>run / idle</code></span>
    </footer>
  </div>
</template>
