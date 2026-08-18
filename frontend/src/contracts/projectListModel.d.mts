export interface ProjectListLocalItem {
  id: string
  name: string
  createdAt: number
  updatedAt: number
  stage: string
}

export interface ProjectListRemoteItem {
  id: string
  name: string
  created_at: string
  updated_at: string
  stage: string
}

export interface ProjectListItem extends ProjectListLocalItem {}

export function mergeProjectListItems(localProjects: ProjectListLocalItem[], remoteProjects: ProjectListRemoteItem[]): ProjectListItem[]
export function relativeUpdatedLabel(updatedAt: number, now?: number): string
export function creationLabel(createdAt: number, now?: number): string
export function isRecentlyCreated(createdAt: number, now?: number): boolean
