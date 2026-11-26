import React from "react";
import { FONT } from "../fonts";
import { Abs, Page, useU, WebImg } from "../kit";

/** Invented fitness web app "Pulse" — dark dashboard, abstract rings and bars; no people. */
export const Fitness: React.FC = () => {
  const u = useU();
  const lime = "#C6F432";
  const card = (x: number, y: number, w: number, h: number, children: React.ReactNode, bg = "#171B22") => (
    <Abs style={{ left: x * u, top: y * u, width: w * u, height: h * u, borderRadius: 26 * u, background: bg, overflow: "hidden" }}>
      {children}
    </Abs>
  );
  const ring = (r: number, frac: number, color: string) => {
    const c = 2 * Math.PI * r;
    return (
      <>
        <circle cx="170" cy="170" r={r} fill="none" stroke={color} strokeOpacity="0.18" strokeWidth="26" />
        <circle
          cx="170"
          cy="170"
          r={r}
          fill="none"
          stroke={color}
          strokeWidth="26"
          strokeLinecap="round"
          strokeDasharray={`${c * frac} ${c}`}
          transform="rotate(-90 170 170)"
        />
      </>
    );
  };
  const bars = [0.55, 0.72, 0.4, 0.86, 0.64, 0.92, 0.3];
  const stat = (x: number, label: string, value: string, unit: string) =>
    card(
      x,
      790,
      400,
      230,
      <div style={{ padding: 34 * u }}>
        <div style={{ fontSize: 18 * u, color: "#8C95A3" }}>{label}</div>
        <div style={{ fontSize: 64 * u, fontWeight: 700, marginTop: 30 * u }}>
          {value}
          <span style={{ fontSize: 24 * u, color: "#8C95A3", fontWeight: 500, marginLeft: 10 * u }}>{unit}</span>
        </div>
      </div>,
    );
  return (
    <Page bg="#0E1116" font={FONT.grotesk} color="#F1F4F8">
      {/* sidebar */}
      <Abs style={{ left: 0, top: 0, width: 112 * u, height: 1080 * u, background: "#12161C", borderRight: `${1 * u}px solid #1F252E` }} />
      <Abs style={{ left: 34 * u, top: 34 * u, width: 44 * u, height: 44 * u, borderRadius: 14 * u, background: lime }} />
      {[180, 260, 340, 420, 500].map((y, i) => (
        <Abs key={y} style={{ left: 40 * u, top: y * u, width: 32 * u, height: 32 * u, borderRadius: 10 * u, border: `${3 * u}px solid ${i === 0 ? lime : "#4A5260"}` }} />
      ))}
      {/* header */}
      <Abs style={{ left: 172 * u, top: 50 * u, fontSize: 22 * u, color: "#8C95A3" }}>Pulse · Today</Abs>
      <Abs style={{ left: 172 * u, top: 86 * u, fontSize: 64 * u, fontWeight: 700 }}>Good morning</Abs>
      <Abs style={{ right: 64 * u, top: 70 * u, background: lime, color: "#0E1116", fontSize: 22 * u, fontWeight: 700, padding: `${18 * u}px ${34 * u}px`, borderRadius: 40 * u }}>
        Start workout
      </Abs>
      {/* rings */}
      {card(
        172,
        210,
        700,
        540,
        <>
          <div style={{ position: "absolute", left: 40 * u, top: 34 * u, fontSize: 26 * u, fontWeight: 600 }}>Activity</div>
          <svg viewBox="0 0 340 340" width={340 * u} height={340 * u} style={{ position: "absolute", left: 30 * u, top: 120 * u }}>
            {ring(150, 0.7, "#FF5A5F")}
            {ring(118, 0.71, lime)}
            {ring(86, 0.75, "#4CC9F0")}
          </svg>
          <div style={{ position: "absolute", left: 410 * u, top: 160 * u, display: "flex", flexDirection: "column", gap: 40 * u }}>
            {[
              ["Move", "420 / 600 kcal", "#FF5A5F"],
              ["Exercise", "32 / 45 min", lime],
              ["Stand", "9 / 12 hours", "#4CC9F0"],
            ].map(([k, v, c]) => (
              <div key={k}>
                <div style={{ fontSize: 20 * u, color: c }}>{k}</div>
                <div style={{ fontSize: 30 * u, fontWeight: 600, marginTop: 4 * u }}>{v}</div>
              </div>
            ))}
          </div>
        </>,
      )}
      {/* weekly bars */}
      {card(
        900,
        210,
        420,
        540,
        <>
          <div style={{ position: "absolute", left: 36 * u, top: 34 * u, fontSize: 26 * u, fontWeight: 600 }}>This week</div>
          {bars.map((b, i) => (
            <React.Fragment key={i}>
              <div
                style={{
                  position: "absolute",
                  left: (40 + i * 52) * u,
                  bottom: 80 * u,
                  width: 30 * u,
                  height: b * 330 * u,
                  borderRadius: 10 * u,
                  background: i === 5 ? lime : "#2C3440",
                }}
              />
              <div style={{ position: "absolute", left: (40 + i * 52) * u, bottom: 36 * u, width: 30 * u, textAlign: "center", fontSize: 18 * u, color: "#8C95A3" }}>
                {"MTWTFSS"[i]}
              </div>
            </React.Fragment>
          ))}
        </>,
      )}
      {/* route card */}
      {card(
        1348,
        210,
        508,
        540,
        <>
          <WebImg name="rural_asphalt_road" pos="50% 62%" zoom={1.6} style={{ inset: 0 }} />
          <div style={{ position: "absolute", inset: 0, background: "linear-gradient(180deg, rgba(14,17,22,0) 35%, rgba(14,17,22,0.9) 100%)" }} />
          <div style={{ position: "absolute", left: 36 * u, bottom: 40 * u }}>
            <div style={{ fontSize: 20 * u, color: lime }}>Suggested route</div>
            <div style={{ fontSize: 40 * u, fontWeight: 700, marginTop: 6 * u }}>Field loop, 5.2 km</div>
            <div style={{ fontSize: 20 * u, color: "#C8CED8", marginTop: 6 * u }}>Flat, quiet road, about 30 minutes</div>
          </div>
        </>,
      )}
      {stat(172, "Resting heart rate", "62", "bpm")}
      {stat(600, "Sleep", "7 h 40", "min")}
      {stat(1028, "Steps", "8,214", "today")}
      {stat(1456, "Water", "1.6", "litres")}
    </Page>
  );
};
