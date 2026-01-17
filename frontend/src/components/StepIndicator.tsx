export default function StepIndicator({ currentStep = 1, totalSteps = 3, completed = false, }) {
  const steps = Array.from({ length: totalSteps }, (_, i) => i + 1);

  return (
    <div className="stepper">
      {steps.map((step, idx) => {
        const isActive = step === currentStep;
        const isDone = step <  currentStep || (step === totalSteps && completed);
        

        return (
          <div className="stepper-item" key={step}>
            <div
              className={[
                "stepper-dot",
                isDone ? "done" : "",
                isActive ? "active" : "",
              ].join(" ")}
            >
              {isDone ? "✓" : step}
            </div>

            {idx !== steps.length - 1 && (
              <div
                className={[
                  "stepper-line",
                  step < currentStep || (step === totalSteps - 1 && completed)
                ].join(" ")}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
