"""Run statistics collection and end-of-run summary."""

from collections import Counter
from dataclasses import dataclass, field

# Fixed display order so the summary line reads the same way on every run
ACTION_ORDER = ["Converted", "Remuxed", "Passed", "Stripped", "Renamed", "Copied", "Processed", "Failed"]

# ffmpeg stderr can run to hundreds of lines; keep one failure on one line
MAX_ERROR_LEN = 200


def _format_elapsed(seconds: float) -> str:
    """Format a duration as MM:SS, or HH:MM:SS once it passes an hour."""
    total = int(round(seconds))
    hours, rem = divmod(total, 3600)
    minutes, secs = divmod(rem, 60)
    if hours:
        return f"{hours:02}:{minutes:02}:{secs:02}"
    return f"{minutes:02}:{secs:02}"


def _condense(error: str) -> str:
    """Collapse a multi-line error into a single truncated line."""
    first = next((line.strip() for line in error.splitlines() if line.strip()), "")
    if len(first) > MAX_ERROR_LEN:
        return first[: MAX_ERROR_LEN - 1] + "…"
    return first


@dataclass
class RunStats:
    """Tallies per-file outcomes so the run can be summarised at the end."""

    images: Counter = field(default_factory=Counter)  # action -> count
    videos: Counter = field(default_factory=Counter)
    failures: list[tuple[str, str]] = field(default_factory=list)  # (source name, error)

    def record(self, counter: Counter, action: str, source_name: str, error: str | None = None) -> None:
        """Record one file's outcome into the given counter (self.images or self.videos)."""
        counter[action] += 1
        if error is not None:
            self.failures.append((source_name, _condense(error)))

    @staticmethod
    def _breakdown(counter: Counter) -> str:
        return "  ".join(f"{action} {counter[action]}" for action in ACTION_ORDER if counter[action])

    def render(self, elapsed: float) -> str:
        """Build the summary text (separate from printing so it can be asserted on)."""
        total_images = sum(self.images.values())
        total_videos = sum(self.videos.values())
        total = total_images + total_videos
        failed = self.images["Failed"] + self.videos["Failed"]

        rows = [("Type", "Count", "Breakdown")]
        if total_images:
            rows.append(("Images", str(total_images), self._breakdown(self.images)))
        if total_videos:
            rows.append(("Videos", str(total_videos), self._breakdown(self.videos)))
        rows.append(("Total", str(total), f"✓ {total - failed}   ✗ {failed}"))

        type_w = max(len(r[0]) for r in rows)
        count_w = max(len(r[1]) for r in rows)
        breakdown_w = max(len(r[2]) for r in rows)

        def border(left: str, mid: str, right: str) -> str:
            return left + mid.join("─" * (w + 2) for w in (type_w, count_w, breakdown_w)) + right

        def row(cols: tuple[str, str, str]) -> str:
            type_col, count_col, breakdown_col = cols
            return f"│ {type_col.ljust(type_w)} │ {count_col.rjust(count_w)} │ {breakdown_col.ljust(breakdown_w)} │"

        lines = ["=== Summary ===", border("┌", "┬", "┐"), row(rows[0]), border("├", "┼", "┤")]
        lines.extend(row(r) for r in rows[1:-1])
        lines.append(border("├", "┼", "┤"))
        lines.append(row(rows[-1]))
        lines.append(border("└", "┴", "┘"))
        lines.append(f"Time    {_format_elapsed(elapsed)}")

        if self.failures:
            name_width = max(len(name) for name, _ in self.failures)
            lines.append("")
            lines.append(f"Failed ({len(self.failures)}):")
            lines.extend(f"  {name.ljust(name_width)}  →  {err}" for name, err in self.failures)

        return "\n".join(lines)

    def print_summary(self, elapsed: float) -> None:
        """Print the end-of-run summary."""
        print(self.render(elapsed))


if __name__ == "__main__":
    stats = RunStats()
    for action in ("Converted", "Converted", "Passed", "Stripped"):
        stats.record(stats.images, action, "x.jpg")
    stats.record(stats.images, "Failed", "broken.jpg", "boom: bad header\nsecond line ignored")
    stats.record(stats.videos, "Remuxed", "a.mov")
    stats.record(stats.videos, "Failed", "bad.avi", "ffmpeg exploded")

    out = stats.render(3725.4)
    print(out)

    assert "│ Images │     5 │ Converted 2  Passed 1  Stripped 1  Failed 1 │" in out, out
    assert "│ Videos │     2 │ Remuxed 1  Failed 1" in out, out
    assert "│ Total  │     7 │ ✓ 5   ✗ 2" in out, out
    assert "Time    01:02:05" in out, out
    assert "Failed (2):" in out, out
    assert "broken.jpg  →  boom: bad header" in out, out
    assert "second line ignored" not in out, out
    assert "Time    00:00" in RunStats().render(0), "empty run should still render"
    print("\nself-check passed")
