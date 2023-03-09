import { CA } from 'api/types';

export async function listCA(): Promise<CA[]> {
  const resp = await fetch(`/abci_query?${new URLSearchParams({ path: '"ca/list"' })}`);
  const data = await resp.json();
  if (data.result.response.code == 0) return JSON.parse(window.atob(data.result.response.value));
  throw 'Cannot get CA list';
}
