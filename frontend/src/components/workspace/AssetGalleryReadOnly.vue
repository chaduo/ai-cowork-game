<script setup lang="ts">
import { Image, LockKeyhole, Music2, Volume2 } from 'lucide-vue-next'
const props = withDefaults(defineProps<{ projectTitle?: string; npcNames?: string[] }>(), { projectTitle: '当前项目', npcNames: () => [] })

const groups = [
  { title: 'Characters', items: [{ name: 'Player', crop: '48% 54%' }, ...props.npcNames.slice(0, 2).map((name, index) => ({ name, crop: index ? '62% 53%' : '58% 50%' }))] },
  { title: 'Environment', items: [{ name: 'Main Scene', crop: '50% 35%' }, { name: 'Interaction Area', crop: '86% 25%' }] },
  { title: 'Gameplay Objects', items: [{ name: 'Interactable A', crop: '18% 42%' }, { name: 'Interactable B', crop: '18% 17%' }, { name: 'Progress Object', crop: '50% 76%' }] },
]
</script>

<template>
  <article class="asset-gallery-readonly">
    <header><div><span>ASSETS · READ ONLY</span><h1>{{ projectTitle }} · First Playable assets</h1><p>当前构建正在使用的 Mock 素材。首个版本完成前不能修改。</p></div><span><LockKeyhole :size="13" />Locked during build</span></header>
    <section v-for="group in groups" :key="group.title">
      <h2>{{ group.title }}</h2>
      <div class="asset-grid">
        <div v-for="item in group.items" :key="item.name" class="asset-tile">
          <div :style="{ backgroundPosition: item.crop }"><Image :size="14" /></div>
          <strong>{{ item.name }}</strong><small>Mock asset · accepted</small>
        </div>
      </div>
    </section>
    <section><h2>Audio</h2><div class="audio-assets"><span><Music2 :size="15" /><b>Ambient BGM</b><small>01:42</small></span><span><Volume2 :size="15" /><b>Interaction SFX</b><small>3 clips</small></span></div></section>
  </article>
</template>
