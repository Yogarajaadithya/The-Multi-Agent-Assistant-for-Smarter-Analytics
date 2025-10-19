import { Tab } from '@headlessui/react';
import { ReactNode } from 'react';
import classNames from 'classnames';

type Props = {
  tabs: Array<{
    label: string;
    content: ReactNode;
    disabled?: boolean;
  }>;
};

export default function Tabs({ tabs }: Props) {
  return (
    <Tab.Group>
      <Tab.List className="flex gap-1 border-b border-gray-800">
        {tabs.map(({ label, disabled }) => (
          <Tab
            key={label}
            disabled={disabled}
            className={({ selected }) =>
              classNames(
                'px-4 py-2 text-sm font-medium outline-none transition-all',
                'border-b-2 -mb-px',
                {
                  'text-indigo-400 border-indigo-400': selected,
                  'text-gray-400 border-transparent hover:text-gray-300 hover:border-gray-700': !selected && !disabled,
                  'text-gray-600 border-transparent cursor-not-allowed': disabled
                }
              )
            }
          >
            {label}
          </Tab>
        ))}
      </Tab.List>
      <Tab.Panels className="mt-4">
        {tabs.map(({ label, content }) => (
          <Tab.Panel key={label} className="outline-none">
            {content}
          </Tab.Panel>
        ))}
      </Tab.Panels>
    </Tab.Group>
  );
}