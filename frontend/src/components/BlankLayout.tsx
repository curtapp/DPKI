import { FC, PropsWithChildren } from 'react';

const BlankLayout: FC<PropsWithChildren> = ({ children }) => (
  <div className="h-screen  flex flex-col gap-2 items-center justify-center">{children}</div>
);
export default BlankLayout;
