import BlankLayout from 'components/BlankLayout';
import { useEffect, useState } from 'react';
import { CA } from 'api/types';
import { listCA } from 'api/methods';

/// Create certificate request
export default function CreateRequest() {
  const [availableCA, setAvailableCA] = useState<CA[]>([]);
  useEffect(() => {
    listCA().then(setAvailableCA);
  }, []);
  return (
    <BlankLayout>
      <form>
        <div className="border-2 m-3 flex flex-col">
          <div className="flex justify-center p-2">
            <span className="capitalize">Request certificate</span>
          </div>
          <div className="p-2">
            {availableCA.length > 0 ? (
              <div className="flex flex-col gap-1">
                <label>Select CA:</label>
                <select name="issuer">
                  {availableCA.map((ca, index) => (
                    <option key={index} value={ca.subject}>
                      {ca.subject}
                    </option>
                  ))}
                </select>
              </div>
            ) : (
              <span>Not found available CA </span>
            )}
          </div>{' '}
        </div>
      </form>
    </BlankLayout>
  );
}
