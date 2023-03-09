import logo from 'assets/logo.svg';
import { FormattedMessage } from 'react-intl';
import { useEffect, useState } from 'react';
import { CA } from 'api/types';
import { listCA } from 'api/methods';

/// Welcome
export default function Welcome() {
  const [itemsCA, setItemsCA] = useState<CA[]>([]);
  useEffect(() => {
    listCA().then(setItemsCA);
  }, []);
  return (
    <div className="h-screen  flex flex-col gap-2 items-center justify-center">
      <img src={logo} className="h-56 w-56" alt="logo" />
      <div className="text-xl">
        <FormattedMessage defaultMessage="The web application" />
        <ul>{itemsCA.length > 0 && itemsCA.map((ca, index) => <li key={index}>{ca.subject}</li>)}</ul>
      </div>
    </div>
  );
}
