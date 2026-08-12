<script setup lang="ts">
import { Braces, ChevronRight, FileCode2, Folder, LockKeyhole } from 'lucide-vue-next'
</script>

<template>
  <article class="code-readonly-state">
    <header><span><LockKeyhole :size="13" />CODE · READ ONLY</span><h1>Source workspace</h1><p>首个 Playable 完成后，这里会开放允许编辑的 GameSpec 和源码文件。</p></header>
    <div class="code-outline">
      <div class="code-tree">
        <strong><Folder :size="14" />多代田园物语</strong>
        <span><ChevronRight :size="12" /><Folder :size="13" />src</span>
        <span class="indent"><FileCode2 :size="13" />main.ts</span>
        <span class="indent"><FileCode2 :size="13" />game-scene.ts</span>
        <span class="indent"><FileCode2 :size="13" />relationship.ts</span>
        <span><ChevronRight :size="12" /><Folder :size="13" />assets</span>
        <span><Braces :size="13" />game-spec.json</span>
      </div>
      <div class="code-placeholder"><FileCode2 :size="24" /><strong>Editor becomes available after Playable v1</strong><p>本阶段只确认 AI Build 与 Validation 是否形成可信闭环。</p></div>
    </div>
  </article>
</template>
