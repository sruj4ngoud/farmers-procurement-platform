import { Check } from 'lucide-react';

export default function BookingProgress({ steps, current }) {
  return (
    <div className="progress-bar">
      {steps.map((step, i) => {
        const isCompleted = i < current;
        const isActive = i === current;
        const cls = isCompleted ? 'completed' : isActive ? 'active' : '';
        return (
          <div key={i} style={{ display: 'flex', alignItems: 'center' }}>
            <div className={`progress-step ${cls}`}>
              <span className="step-num">
                {isCompleted ? <Check size={12} /> : i + 1}
              </span>
              <span>{step.label}</span>
            </div>
            {i < steps.length - 1 && (
              <div className={`progress-connector ${isCompleted ? 'done' : ''}`} />
            )}
          </div>
        );
      })}
    </div>
  );
}
