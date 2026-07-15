import Link from 'next/link';
import { CompassIcon } from 'lucide-react';
import { EmptyState } from '@/components/shared/EmptyState';
import { Button } from '@/components/ui/Button';

export default function NotFound() {
  return (
    <div className="mx-auto max-w-2xl px-4 py-16">
      <EmptyState
        icon={CompassIcon}
        title="Page not found"
        description="This page doesn't exist, or the coin you're looking for isn't tracked."
        action={
          <Link href="/">
            <Button variant="accent" size="sm">
              Back to screener
            </Button>
          </Link>
        }
      />
    </div>
  );
}
