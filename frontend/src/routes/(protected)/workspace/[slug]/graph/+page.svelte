<script lang="ts">
  import { goto } from '$app/navigation';
  import GraphView from '$lib/components/GraphView.svelte';
  import type { AnyGraphNode } from '$lib/graph/model';
  import { graphPath, noteInTreePath } from '$lib/routes';

  let { data } = $props();
  const slug = $derived(data.slug);
  const graph = $derived(data.graph);
  const includeTags = $derived(data.includeTags);

  function handleNodeClick(node: AnyGraphNode): void {
    if (node.kind !== 'note') return;
    goto(noteInTreePath(node.workspace ?? slug, node.folder, node.note_id));
  }

  function toggleTags(): void {
    // eslint-disable-next-line svelte/no-navigation-without-resolve
    goto(graphPath(slug, !includeTags), { replaceState: true });
  }
</script>

<main class="graph-page">
  <header class="graph-page__header">
    <div>
      <p class="graph-page__workspace">{slug}</p>
      <h1>Graf workspace’u</h1>
    </div>
    <label class="graph-page__toggle">
      <input type="checkbox" checked={includeTags} onchange={toggleTags} />
      <span>Pokaż tagi</span>
    </label>
  </header>

  {#if graph.nodes.length === 0}
    <p class="graph-page__empty">Brak notatek w tym workspace’ie.</p>
  {:else}
    <section class="graph-page__canvas" aria-label="Graf notatek workspace’u">
      {#key graph}
        <GraphView data={graph} onNodeClick={handleNodeClick} />
      {/key}
    </section>
  {/if}
</main>

<style lang="scss">
  @use '$lib/styles/variables' as v;
  @use '$lib/styles/breakpoints' as bp;

  .graph-page {
    display: flex;
    flex-direction: column;
    height: calc(100dvh - 48px);
    padding: v.$space-lg;
    box-sizing: border-box;

    &__header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: v.$space-md;
      flex-shrink: 0;
      margin-bottom: v.$space-md;
    }

    &__workspace {
      margin: 0 0 v.$space-xs;
      color: v.$text-muted;
      font-family: v.$font-mono;
      font-size: 0.72rem;
    }

    h1 {
      margin: 0;
      color: v.$text-primary;
      font-family: v.$font-mono;
      font-size: 1.2rem;
    }

    &__toggle {
      display: flex;
      align-items: center;
      gap: v.$space-xs;
      color: v.$text-secondary;
      cursor: pointer;
      font-family: v.$font-mono;
      font-size: 0.75rem;
      white-space: nowrap;
    }

    &__canvas {
      flex: 1;
      min-height: 0;
      min-width: 0;
      overflow: hidden;
      border: 1px solid v.$border;
      border-radius: v.$radius-lg;
      background: v.$bg-surface;
    }

    &__empty {
      margin: auto;
      color: v.$text-muted;
      font-family: v.$font-mono;
      font-size: 0.85rem;
    }
  }

  @include bp.mobile {
    .graph-page {
      height: calc(100dvh - 48px);
      padding: v.$space-md;

      &__header {
        align-items: flex-start;
        flex-direction: column;
      }

      &__canvas {
        min-height: 0;
      }
    }
  }
</style>
