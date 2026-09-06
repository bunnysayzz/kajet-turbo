import { error, redirect } from '@sveltejs/kit';
import { apiNoteGraphApiWorkspacesNameNotesGraphGet } from '$lib/api';
import { loginPath, workspacesPath } from '$lib/routes';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ params, url }) => {
  const slug = params.slug;
  const includeTags = url.searchParams.get('tags') === '1';

  let result;
  try {
    result = await apiNoteGraphApiWorkspacesNameNotesGraphGet(slug, {
      include_tags: includeTags,
    });
  } catch (e) {
    const status = (e as { status?: number }).status;
    if (status === 401) redirect(307, loginPath());
    if (status === 403) redirect(307, workspacesPath());
    error(500, 'Nie udało się pobrać grafu workspace’u.');
  }

  if (result.status !== 200) error(500, 'Nie udało się pobrać grafu workspace’u.');

  return {
    slug,
    graph: result.data,
    includeTags,
  };
};
