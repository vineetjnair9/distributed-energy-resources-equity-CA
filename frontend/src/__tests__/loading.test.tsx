import { act, render, screen } from "@testing-library/react";
import { inflight } from "../api/inflight";
import { Busy, ProgressBar } from "../components/Busy";

describe("loading feedback", () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => vi.useRealTimers());

  it("shows the progress bar only for requests that outlast the delay", async () => {
    const { container } = render(<ProgressBar />);
    const bar = () => container.querySelector(".progress")!;
    let finish!: () => void;
    let tracked!: Promise<void>;
    act(() => {
      tracked = inflight.track(new Promise<void>((resolve) => (finish = resolve)));
    });
    expect(bar()).not.toHaveClass("progress-on");
    act(() => vi.advanceTimersByTime(200));
    expect(bar()).toHaveClass("progress-on");
    expect(screen.getByRole("status")).toHaveTextContent("Loading");
    await act(async () => {
      finish();
      await tracked;
    });
    expect(bar()).not.toHaveClass("progress-on");
  });

  it("dims replaced content while loading and marks it busy", () => {
    const { rerender, container } = render(<Busy when={false}><p>Old results</p></Busy>);
    const region = () => container.querySelector(".busy-region")!;
    rerender(<Busy when={true}><p>Old results</p></Busy>);
    expect(region()).toHaveAttribute("aria-busy", "true");
    expect(region()).not.toHaveClass("is-busy");
    act(() => vi.advanceTimersByTime(200));
    expect(region()).toHaveClass("is-busy");
    rerender(<Busy when={false}><p>New results</p></Busy>);
    expect(region()).not.toHaveClass("is-busy");
    expect(region()).toHaveAttribute("aria-busy", "false");
  });
});
