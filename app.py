"""TemporalGuard entry point."""

from __future__ import annotations

from temporalguard.pipeline.orchestrator import run_pipeline


def main() -> None:
    result = run_pipeline("What is TemporalGuard?")
    print(result)


if __name__ == "__main__":
    main()
