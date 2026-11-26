import React from "react";
import { FONT } from "../fonts";
import { Abs, Page, useU } from "../kit";

/** Invented home-goods store "Oakline Home" — unbranded products drawn as vector still lifes. */
export const Store: React.FC = () => {
  const u = useU();
  const ink = "#22201C";
  const product = (
    x: number,
    name: string,
    price: string,
    tone: string,
    art: React.ReactNode,
  ) => (
    <Abs style={{ left: x * u, top: 760 * u, width: 420 * u }}>
      <div style={{ height: 330 * u, borderRadius: 18 * u, background: tone, position: "relative", overflow: "hidden" }}>
        <svg viewBox="0 0 420 330" width={420 * u} height={330 * u} style={{ position: "absolute", inset: 0 }}>
          {art}
        </svg>
      </div>
      <div style={{ display: "flex", justifyContent: "space-between", marginTop: 16 * u, fontSize: 21 * u }}>
        <span style={{ fontWeight: 500 }}>{name}</span>
        <span style={{ fontWeight: 700 }}>{price}</span>
      </div>
    </Abs>
  );
  const shadow = <ellipse cx="210" cy="292" rx="110" ry="14" fill="rgba(0,0,0,0.10)" />;
  return (
    <Page bg="#FFFFFF" font={FONT.inter} color={ink}>
      <Abs
        style={{
          left: 0,
          top: 0,
          width: 1920 * u,
          height: 44 * u,
          background: ink,
          color: "#EDE7DD",
          fontSize: 16 * u,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          letterSpacing: 1 * u,
        }}
      >
        Free delivery on every order over 60 — this week only
      </Abs>
      <Abs style={{ left: 64 * u, top: 74 * u, fontFamily: FONT.grotesk, fontWeight: 700, fontSize: 34 * u, letterSpacing: 6 * u }}>
        OAKLINE
      </Abs>
      <Abs style={{ left: 640 * u, top: 84 * u, display: "flex", gap: 46 * u, fontSize: 19 * u, fontWeight: 500 }}>
        {["Living", "Kitchen", "Lighting", "Textiles", "Outdoor", "Sale"].map((t) => (
          <span key={t} style={{ color: t === "Sale" ? "#B5482F" : ink }}>
            {t}
          </span>
        ))}
      </Abs>
      {/* generic icons: search + bag */}
      <svg viewBox="0 0 100 30" width={100 * u} height={30 * u} style={{ position: "absolute", right: 64 * u, top: 80 * u }}>
        <circle cx="12" cy="12" r="8" fill="none" stroke={ink} strokeWidth="2.4" />
        <line x1="18" y1="18" x2="25" y2="25" stroke={ink} strokeWidth="2.4" strokeLinecap="round" />
        <path d="M66 9 h22 l-2 19 h-18 z" fill="none" stroke={ink} strokeWidth="2.4" strokeLinejoin="round" />
        <path d="M71 9 a6 6 0 0 1 12 0" fill="none" stroke={ink} strokeWidth="2.4" />
      </svg>
      {/* hero */}
      <Abs style={{ left: 64 * u, top: 160 * u, width: 1792 * u, height: 540 * u, borderRadius: 26 * u, background: "#EFE8DD" }} />
      <Abs style={{ left: 140 * u, top: 250 * u, width: 760 * u }}>
        <div style={{ fontSize: 18 * u, letterSpacing: 4 * u, fontWeight: 600, color: "#8C7A63" }}>NEW SEASON</div>
        <div style={{ fontSize: 84 * u, fontWeight: 700, lineHeight: 1.02, marginTop: 16 * u, letterSpacing: -2 * u }}>
          Calm colours for slow mornings
        </div>
        <div style={{ fontSize: 23 * u, marginTop: 22 * u, color: "#5C554B", lineHeight: 1.45 }}>
          Stoneware, linen and solid oak, made in small batches.
        </div>
        <div style={{ display: "flex", gap: 18 * u, marginTop: 36 * u }}>
          <div style={{ background: ink, color: "white", padding: `${20 * u}px ${36 * u}px`, borderRadius: 10 * u, fontSize: 20 * u, fontWeight: 600 }}>
            Shop the collection
          </div>
          <div style={{ border: `${2 * u}px solid ${ink}`, padding: `${18 * u}px ${34 * u}px`, borderRadius: 10 * u, fontSize: 20 * u, fontWeight: 600 }}>
            Lookbook
          </div>
        </div>
      </Abs>
      {/* still life: table top, vase with branch, sphere lamp, stacked bowls */}
      <svg viewBox="0 0 900 540" width={900 * u} height={540 * u} style={{ position: "absolute", left: 940 * u, top: 160 * u }}>
        <defs>
          <radialGradient id="lamp" cx="40%" cy="35%" r="70%">
            <stop offset="0" stopColor="#FFF8E8" />
            <stop offset="0.6" stopColor="#F4DDB0" />
            <stop offset="1" stopColor="#D9B67A" />
          </radialGradient>
          <linearGradient id="vase" x1="0" x2="1">
            <stop offset="0" stopColor="#B9A48A" />
            <stop offset="0.45" stopColor="#D8C8B2" />
            <stop offset="1" stopColor="#9E8A70" />
          </linearGradient>
        </defs>
        <rect x="60" y="430" width="800" height="26" rx="6" fill="#B98B5E" />
        <rect x="60" y="452" width="800" height="12" fill="#9E7449" />
        <path d="M250 430 C 200 430 190 360 215 320 C 235 290 228 250 240 230 L 280 230 C 292 250 285 290 305 320 C 330 360 320 430 270 430 Z" fill="url(#vase)" />
        <path d="M262 232 C 270 170 300 120 350 80 M 290 150 C 320 140 340 150 360 135 M 275 190 C 250 160 230 150 205 150" stroke="#5E4B36" strokeWidth="4" fill="none" strokeLinecap="round" />
        {[
          [350, 80],
          [360, 135],
          [205, 150],
          [320, 105],
          [240, 165],
        ].map(([x, y], i) => (
          <ellipse key={i} cx={x} cy={y} rx="16" ry="8" transform={`rotate(${-30 + i * 25} ${x} ${y})`} fill="#7E8F5B" />
        ))}
        <circle cx="560" cy="330" r="100" fill="url(#lamp)" />
        <rect x="545" y="420" width="30" height="12" rx="3" fill="#8A6E4B" />
        <path d="M660 430 h150 l-12 -36 h-126 z" fill="#E7E1D6" />
        <path d="M675 394 h120 l-10 -30 h-100 z" fill="#C9B9A3" />
        <path d="M690 364 h90 l-8 -24 h-74 z" fill="#8F7F69" />
      </svg>
      {product(
        64,
        "Stoneware mug",
        "18.00",
        "#F3EEE6",
        <>
          {shadow}
          <rect x="160" y="140" width="100" height="140" rx="16" fill="#CDBBA2" />
          <path d="M260 175 h22 a26 26 0 0 1 0 52 h-22" fill="none" stroke="#CDBBA2" strokeWidth="16" />
        </>,
      )}
      {product(
        522,
        "Linen cushion",
        "34.00",
        "#E9EDE6",
        <>
          {shadow}
          <path d="M110 120 Q 210 100 310 120 Q 330 200 310 280 Q 210 300 110 280 Q 90 200 110 120 Z" fill="#A9B79A" />
          <path d="M120 200 Q 210 190 300 200" stroke="#97A688" strokeWidth="3" fill="none" />
        </>,
      )}
      {product(
        980,
        "Oak side table",
        "149.00",
        "#F4EFE8",
        <>
          {shadow}
          <ellipse cx="210" cy="130" rx="110" ry="22" fill="#B98B5E" />
          <rect x="198" y="130" width="24" height="150" fill="#9E7449" />
          <ellipse cx="210" cy="282" rx="60" ry="10" fill="#9E7449" />
        </>,
      )}
      {product(
        1438,
        "Globe table lamp",
        "89.00",
        "#EFEAF0",
        <>
          {shadow}
          <circle cx="210" cy="160" r="80" fill="url(#lamp)" />
          <rect x="196" y="240" width="28" height="40" rx="6" fill="#6B5E52" />
        </>,
      )}
    </Page>
  );
};
