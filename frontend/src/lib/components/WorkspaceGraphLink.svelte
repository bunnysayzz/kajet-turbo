<script lang="ts">
  import { page } from '$app/state';
  import { graphPath } from '$lib/routes';

  let {
    slug,
    variant,
  }: {
    slug: string;
    variant: 'navbar' | 'sidebar';
  } = $props();

  const active = $derived(page.url.pathname === `/workspace/${slug}/graph`);
</script>

<!-- eslint-disable svelte/no-navigation-without-resolve -->
<a
  href={graphPath(slug)}
  class="graph-link"
  class:graph-link--navbar={variant === 'navbar'}
  class:graph-link--sidebar={variant === 'sidebar'}
  class:graph-link--active={active}
  aria-current={active ? 'page' : undefined}
>
  {#if variant === 'sidebar'}◎ Graf workspace’u{:else}Graf{/if}
</a>

<!-- eslint-enable svelte/no-navigation-without-resolve -->

<style lang="scss">
  @use '$lib/styles/variables' as v;
  @use '$lib/styles/effects' as fx;

  .graph-link {
    color: v.$text-muted;
    font-family: v.$font-mono;
    text-decoration: none;
    transition: color 0.15s;

    &:hover {
      color: v.$text-secondary;
    }
  }

  :global(.graph-link--navbar) {
    padding: 4px 10px;
    border-radius: v.$radius-md;
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
  }

  :global(.graph-link--sidebar) {
    flex-shrink: 0;
    padding: 10px 12px;
    font-size: 0.72rem;
  }

  :global(.graph-link--active) {
    color: v.$accent;
    background: rgba(240, 184, 0, 0.08);
    border: 1px solid rgba(240, 184, 0, 0.15);
  }

  :global(.graph-link--active.graph-link--navbar) {
    @include fx.glow(v.$accent, 0.25);
  }
</style>
