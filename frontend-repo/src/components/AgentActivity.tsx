import { AgentName } from '../lib/api';
import classNames from 'classnames';
import { CheckCircleIcon, ClockIcon } from '@heroicons/react/24/solid';

type Props = {
  activity: Array<{
    agent: AgentName;
    status: 'pending' | 'running' | 'done';
  }>;
};

const AGENT_LABELS: Record<AgentName, string> = {
  planner: 'Planner',
  eda: 'EDA',
  stats: 'Stats',
  simulation: 'Simulation',
  viz: 'Viz',
  insights: 'Insights'
};

export default function AgentActivity({ activity }: Props) {
  return (
    <div className="flex items-center justify-center gap-4 py-4">
      {activity.map(({ agent, status }) => (
        <div
          key={agent}
          className={classNames(
            'flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium transition-all',
            {
              'text-gray-400 bg-gray-800/50': status === 'pending',
              'text-indigo-200 bg-indigo-500/20 animate-pulse': status === 'running',
              'text-green-200 bg-green-500/20': status === 'done'
            }
          )}
        >
          {status === 'done' ? (
            <CheckCircleIcon className="w-4 h-4" />
          ) : (
            <ClockIcon className={classNames('w-4 h-4', {
              'animate-spin': status === 'running'
            })} />
          )}
          {AGENT_LABELS[agent]}
        </div>
      ))}
    </div>
  );
}