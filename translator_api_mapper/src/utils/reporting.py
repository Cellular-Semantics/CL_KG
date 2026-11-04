"""Per-step result reporting.

Failures never stop the pipeline (every step is safe to re-run), but they must
be visible: each step returns a StepReport and pipeline_mapper logs a summary.
"""
import logging
from dataclasses import dataclass, field


@dataclass
class BatchResult:
    """Outcome of sending one SPARQL update batch."""

    statements: int = 0  # statements in the request that was sent
    skipped: int = 0  # invalid items dropped before sending
    error: str | None = None  # set when the request failed or was rejected


@dataclass
class StepReport:
    step: str
    batches_ok: int = 0
    statements_ok: int = 0
    skipped: int = 0
    failures: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.failures

    def add_batch(self, batch_no: int, result: BatchResult) -> None:
        self.skipped += result.skipped
        if result.error:
            self.failures.append(f"batch {batch_no}: {result.error}")
        elif result.statements:
            self.batches_ok += 1
            self.statements_ok += result.statements

    def fail(self, message: str) -> None:
        self.failures.append(message)

    def log_summary(self, logger: logging.Logger) -> None:
        summary = (
            f"[{self.step}] {self.batches_ok} batch(es) / {self.statements_ok} "
            f"statement(s) written, {self.skipped} invalid item(s) skipped, "
            f"{len(self.failures)} failure(s)"
        )
        if self.ok:
            logger.info(summary)
            return
        logger.error(summary)
        for failure in self.failures:
            logger.error(f"[{self.step}]   {failure}")
