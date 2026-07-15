import { ExternalLink } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';

export function ExplorerLinks({ links }: { links: any }) {
  const homepage: string[] = (links?.homepage ?? []).filter(Boolean);
  const explorers: string[] = (links?.blockchain_site ?? []).filter(Boolean);
  const social = [
    links?.twitter_screen_name && `https://twitter.com/${links.twitter_screen_name}`,
    links?.subreddit_url,
    links?.repos_url?.github?.[0],
  ].filter(Boolean) as string[];

  const all = [...homepage, ...explorers.slice(0, 4), ...social];

  if (all.length === 0) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Links</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-wrap gap-2">
        {all.map((url) => (
          <a
            key={url}
            href={url}
            target="_blank"
            rel="noreferrer noopener"
            className="focus-ring flex items-center gap-1.5 rounded-lg border border-base-border bg-base-raised px-3 py-1.5 text-xs text-neutral hover:text-base-50"
          >
            <ExternalLink size={12} />
            {new URL(url).hostname.replace('www.', '')}
          </a>
        ))}
      </CardContent>
    </Card>
  );
}
