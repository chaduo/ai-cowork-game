<script setup lang="ts">
import { Image, LockKeyhole, Music2, Volume2 } from 'lucide-vue-next'

const groups = [
  { title: 'Characters', items: [{ name: 'Player', crop: '48% 54%' }, { name: 'Lucy', crop: '62% 53%' }] },
  { title: 'Environment', items: [{ name: 'Farm Background', crop: '50% 35%' }, { name: 'Market Stall', crop: '86% 25%' }] },
  { title: 'Animals & Crops', items: [{ name: 'Chicken', crop: '18% 42%' }, { name: 'Cow', crop: '18% 17%' }, { name: 'Wheat', crop: '50% 76%' }] },
]
</script>

<template>
  <article class="asset-gallery-readonly">
    <header><div><span>ASSETS · READ ONLY</span><h1>First Playable assets</h1><p>当前构建正在使用的 Mock 素材。首个版本完成前不能修改。</p></div><span><LockKeyhole :size="13" />Locked during build</span></header>
    <section v-for="group in groups" :key="group.title">
      <h2>{{ group.title }}</h2>
      <div class="asset-grid">
        <div v-for="item in group.items" :key="item.name" class="asset-tile">
          <div :style="{ backgroundPosition: item.crop }"><Image :size="14" /></div>
          <strong>{{ item.name }}</strong><small>Mock asset · accepted</small>
        </div>
      </div>
    </section>
    <section><h2>Audio</h2><div class="audio-assets"><span><Music2 :size="15" /><b>Farm Morning BGM</b><small>01:42</small></span><span><Volume2 :size="15" /><b>Harvest & Coin SFX</b><small>3 clips</small></span></div></section>
  </article>
</template>
