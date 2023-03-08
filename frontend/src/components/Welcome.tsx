import logo from 'assets/logo.svg';
import { FormattedMessage } from 'react-intl';

/// Welcome
export default function Welcome() {
  return (
    <div className="h-screen  flex flex-col gap-2 items-center justify-center">
      <img src={logo} className="h-56 w-56" alt="logo" />
      <div className="text-xl">
        <FormattedMessage defaultMessage="The web application" />
      </div>
    </div>
  );
}
