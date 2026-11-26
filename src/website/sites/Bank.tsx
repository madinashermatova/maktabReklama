import React from "react";
import { FONT } from "../fonts";
import { Abs, Page, useU } from "../kit";

/** Invented banking dashboard "Ledgerly" — generic figures, no currency symbol, no real bank. */
export const Bank: React.FC = () => {
  const u = useU();
  const ink = "#101828";
  const blue = "#3355FF";
  const card = (x: number, y: number, w: number, h: number, children: React.ReactNode, bg = "white") => (
    <Abs style={{ left: x * u, top: y * u, width: w * u, height: h * u, background: bg, borderRadius: 20 * u, boxShadow: `0 ${2 * u}px ${10 * u}px rgba(16,24,40,0.06)`, overflow: "hidden" }}>
      {children}
    </Abs>
  );
  const inc = [40, 52, 48, 66, 61, 78, 74];
  const exp = [30, 34, 41, 38, 45, 42, 47];
  const path = (vals: number[]) =>
    vals.map((v, i) => `${i === 0 ? "M" : "L"} ${60 + i * 145} ${300 - v * 3}`).join(" ");
  const tx: [string, string, string][] = [
    ["Grocery market", "Food", "−54.20"],
    ["Electricity bill", "Home", "−38.00"],
    ["Salary deposit", "Income", "+2,400.00"],
    ["Coffee shop", "Food", "−4.50"],
    ["Bookshop", "Leisure", "−21.90"],
  ];
  return (
    <Page bg="#F3F5F8" font={FONT.inter} color={ink}>
      <Abs style={{ left: 0, top: 0, width: 300 * u, height: 1080 * u, background: "white", borderRight: `${1 * u}px solid #E4E7EC` }} />
      <Abs style={{ left: 44 * u, top: 40 * u, fontSize: 30 * u, fontWeight: 800, letterSpacing: -0.5 * u }}>
        Ledgerly
      </Abs>
      <Abs style={{ left: 28 * u, top: 130 * u, width: 244 * u, display: "flex", flexDirection: "column", gap: 6 * u }}>
        {["Overview", "Accounts", "Cards", "Payments", "Savings", "Reports", "Settings"].map((t, i) => (
          <div key={t} style={{ padding: `${14 * u}px ${18 * u}px`, borderRadius: 10 * u, fontSize: 19 * u, fontWeight: i === 0 ? 700 : 500, background: i === 0 ? "#EEF1FF" : "transparent", color: i === 0 ? blue : "#475467" }}>
            {t}
          </div>
        ))}
      </Abs>
      <Abs style={{ left: 360 * u, top: 44 * u, fontSize: 44 * u, fontWeight: 700 }}>Overview</Abs>
      <Abs style={{ right: 64 * u, top: 44 * u, width: 420 * u, height: 54 * u, borderRadius: 12 * u, background: "white", border: `${1 * u}px solid #E4E7EC`, fontSize: 18 * u, color: "#98A2B3", display: "flex", alignItems: "center", paddingLeft: 20 * u }}>
        Search payments and accounts
      </Abs>
      {card(
        360,
        140,
        520,
        230,
        <div style={{ padding: 34 * u, color: "white" }}>
          <div style={{ fontSize: 19 * u, opacity: 0.8 }}>Total balance</div>
          <div style={{ fontSize: 60 * u, fontWeight: 700, marginTop: 12 * u }}>12,480.50</div>
          <div style={{ fontSize: 18 * u, opacity: 0.8, marginTop: 18 * u }}>Main account · **** 2048</div>
        </div>,
        `linear-gradient(135deg, ${blue}, #6C3BFF)`,
      )}
      {card(
        904,
        140,
        460,
        230,
        <div style={{ padding: 34 * u }}>
          <div style={{ fontSize: 19 * u, color: "#667085" }}>Spent this month</div>
          <div style={{ fontSize: 52 * u, fontWeight: 700, marginTop: 12 * u }}>1,932.10</div>
          <div style={{ marginTop: 26 * u, height: 12 * u, borderRadius: 6 * u, background: "#EEF1F6" }}>
            <div style={{ width: "62%", height: "100%", borderRadius: 6 * u, background: "#F79009" }} />
          </div>
        </div>,
      )}
      {card(
        1388,
        140,
        468,
        230,
        <div style={{ padding: 34 * u }}>
          <div style={{ fontSize: 19 * u, color: "#667085" }}>Savings goal</div>
          <div style={{ fontSize: 52 * u, fontWeight: 700, marginTop: 12 * u }}>64%</div>
          <div style={{ fontSize: 18 * u, color: "#12B76A", marginTop: 18 * u }}>On track for the summer</div>
        </div>,
      )}
      {card(
        360,
        396,
        1004,
        640,
        <>
          <div style={{ position: "absolute", left: 34 * u, top: 30 * u, fontSize: 26 * u, fontWeight: 700 }}>Cash flow</div>
          <div style={{ position: "absolute", right: 34 * u, top: 34 * u, display: "flex", gap: 26 * u, fontSize: 17 * u, color: "#475467" }}>
            <span style={{ color: blue }}>
              <span style={{ display: "inline-block", width: 10 * u, height: 10 * u, borderRadius: "50%", background: blue, marginRight: 8 * u }} />
              Income
            </span>
            <span style={{ color: "#F79009" }}>
              <span style={{ display: "inline-block", width: 10 * u, height: 10 * u, borderRadius: "50%", background: "#F79009", marginRight: 8 * u }} />
              Expenses
            </span>
          </div>
          <svg viewBox="0 0 1004 520" width={1004 * u} height={520 * u} style={{ position: "absolute", left: 0, top: 100 * u }}>
            {[0, 1, 2, 3, 4].map((k) => (
              <line key={k} x1="40" x2="980" y1={60 + k * 70} y2={60 + k * 70} stroke="#EAECF0" strokeWidth="1.5" />
            ))}
            <path d={`${path(inc)} L 930 300 L 60 300 Z`} fill={blue} fillOpacity="0.08" />
            <path d={path(inc)} fill="none" stroke={blue} strokeWidth="4" strokeLinejoin="round" />
            <path d={path(exp)} fill="none" stroke="#F79009" strokeWidth="4" strokeLinejoin="round" />
            {["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul"].map((m, i) => (
              <text key={m} x={60 + i * 145} y="360" fontSize="18" fill="#98A2B3" fontFamily={FONT.inter} textAnchor="middle">
                {m}
              </text>
            ))}
          </svg>
        </>,
      )}
      {card(
        1388,
        396,
        468,
        640,
        <div style={{ padding: 34 * u }}>
          <div style={{ fontSize: 26 * u, fontWeight: 700, marginBottom: 20 * u }}>Recent activity</div>
          {tx.map(([n, c, a]) => (
            <div key={n} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: `${18 * u}px 0`, borderBottom: `${1 * u}px solid #EAECF0` }}>
              <div>
                <div style={{ fontSize: 20 * u, fontWeight: 600 }}>{n}</div>
                <div style={{ fontSize: 16 * u, color: "#98A2B3", marginTop: 4 * u }}>{c}</div>
              </div>
              <div style={{ fontSize: 20 * u, fontWeight: 700, color: a.startsWith("+") ? "#12B76A" : ink }}>{a}</div>
            </div>
          ))}
        </div>,
      )}
    </Page>
  );
};
