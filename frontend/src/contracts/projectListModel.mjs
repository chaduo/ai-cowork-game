function timestamp(value, fallback) {
  const parsed = typeof value === 'number' ? value : Date.parse(value ?? '')
  return Number.isFinite(parsed) ? parsed : fallback
}

export function mergeProjectListItems(localProjects, remoteProjects) {
  const remoteById = new Map(remoteProjects.map((project) => [project.id, project]))
  const local = localProjects.map((project) => {
    const remote = remoteById.get(project.id)
    return remote
      ? {
          id: project.id,
          name: remote.name,
          createdAt: timestamp(remote.created_at, project.createdAt),
          updatedAt: timestamp(remote.updated_at, project.updatedAt),
          stage: remote.stage,
        }
      : project
  })
  const localIds = new Set(local.map((project) => project.id))
  const remoteOnly = remoteProjects
    .filter((project) => !localIds.has(project.id))
    .map((project) => {
      const createdAt = timestamp(project.created_at, timestamp(project.updated_at, 0))
      return {
        id: project.id,
        name: project.name,
        createdAt,
        updatedAt: timestamp(project.updated_at, createdAt),
        stage: project.stage,
      }
    })
  return [...local, ...remoteOnly].sort((left, right) => right.updatedAt - left.updatedAt)
}

export function relativeUpdatedLabel(updatedAt, now = Date.now()) {
  const elapsedMinutes = Math.max(0, Math.floor((now - updatedAt) / 60_000))
  if (elapsedMinutes < 1) return '刚刚更新'
  if (elapsedMinutes < 60) return `${elapsedMinutes} 分钟前更新`
  const elapsedHours = Math.floor(elapsedMinutes / 60)
  if (elapsedHours < 24) return `${elapsedHours} 小时前更新`
  return `${Math.floor(elapsedHours / 24)} 天前更新`
}

export function creationLabel(createdAt, now = Date.now()) {
  const created = new Date(createdAt)
  if (!Number.isFinite(created.getTime())) return '创建时间未知'
  const time = created.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', hour12: false })
  const elapsedHours = Math.max(0, (now - createdAt) / 3_600_000)
  if (elapsedHours < 1) return `刚创建 · ${time}`
  if (created.toDateString() === new Date(now).toDateString()) return `今天 ${time} 创建`
  return `${created.getMonth() + 1}月${created.getDate()}日创建`
}

export function isRecentlyCreated(createdAt, now = Date.now()) {
  return now - createdAt < 10 * 60_000
}
