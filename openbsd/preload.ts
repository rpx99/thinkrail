if (process.platform === "openbsd") {
	globalThis.queueMicrotask = (callback: VoidFunction): void => {
		if (typeof callback !== "function") throw new TypeError("callback must be a function");
		void Promise.resolve()
			.then(() => callback())
			.catch((error: unknown) => {
				setTimeout(() => {
					throw error;
				}, 0);
			});
	};

	const NativeResponse = globalThis.Response;
	globalThis.Response = class extends NativeResponse {
		static [Symbol.hasInstance](value: unknown): boolean {
			return value instanceof NativeResponse;
		}

		constructor(body?: BodyInit | null, init?: ResponseInit) {
			if (body instanceof Blob && typeof (body as { exists?: unknown }).exists === "function") {
				const headers = new Headers(init?.headers);
				if (body.type && !headers.has("Content-Type")) headers.set("Content-Type", body.type);
				super(body.stream(), { ...init, headers });
			} else {
				super(body, init);
			}
		}
	};
}
