"use client";

import * as React from "react";

export function useElementSize<T extends HTMLElement>() {
    const ref = React.useRef<T | null>(null);
    const [size, setSize] = React.useState({ width: 0, height: 0 });

    React.useEffect(() => {
        if (!ref.current) return;
        const el = ref.current;
        const obs = new ResizeObserver((entries) => {
            const box = entries[0]?.contentRect;
            if (!box) return;
            setSize({ width: box.width, height: box.height });
        });
        obs.observe(el);
        return () => obs.disconnect();
    }, []);

    return { ref, size } as const;
}