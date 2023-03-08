import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './tailwind.css';
import { IntlProvider } from 'react-intl';

async function resourceLoader(): Promise<{ locale: string; messages: any }> {
  const locale = navigator.language;
  switch (locale) {
    case 'ru':
    case 'ru-RU':
      return { locale: 'ru', messages: await import('messages/compiled/ru.json') };
    default:
      return { locale: 'en', messages: await import('messages/compiled/en.json') };
  }
}

const container = document.getElementById('root');
if (!container) throw new Error('Cannot create react root');
const root = ReactDOM.createRoot(container);
resourceLoader().then(({ locale, messages }) =>
  root.render(
    <React.StrictMode>
      <IntlProvider messages={messages} locale={locale} defaultLocale="ru">
        <App />
      </IntlProvider>
    </React.StrictMode>
  )
);
