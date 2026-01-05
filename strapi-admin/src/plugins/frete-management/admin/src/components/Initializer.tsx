import { useEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom';

type InitializerProps = {
  setPlugin: (id: string) => void;
};

const Initializer = ({ setPlugin }: InitializerProps) => {
  const { pathname } = useLocation();
  const ref = useRef(false);

  useEffect(() => {
    if (!ref.current) {
      setPlugin('frete-management');
      ref.current = true;
    }
  }, [pathname, setPlugin]);

  return null;
};

export { Initializer };




