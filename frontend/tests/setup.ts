import "@testing-library/jest-dom"
import { vi } from "vitest"

Object.defineProperty(window, "localStorage", {
  value: {
    getItem: vi.fn(),
    setItem: vi.fn(),
    removeItem: vi.fn(),
  },
  writable: true,
})

HTMLCanvasElement.prototype.getContext = vi.fn()

class MockResizeObserver {
  observe = vi.fn()
  unobserve = vi.fn()
  disconnect = vi.fn()
}

Object.defineProperty(window, "ResizeObserver", {
  value: MockResizeObserver,
  writable: true,
})

const originalConsoleError = console.error
console.error = (...args) => {
  if (
    typeof args[0] === "string" &&
    args[0].includes("Warning: ReactDOM.render is no longer supported")
  ) {
    return
  }
  originalConsoleError.call(console, ...args)
}
