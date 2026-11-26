import React from "react";
import { FONT } from "../fonts";
import { Abs, Page, useU, WebImg } from "../kit";

/** Invented news portal "The Daily Meridian" — neutral, invented headlines; no real places or people. */
export const News: React.FC = () => {
  const u = useU();
  const ink = "#141414";
  const rule = (top: number, left = 64, width = 1792, weight = 1) => (
    <Abs style={{ left: left * u, top: top * u, width: width * u, height: weight * u, background: ink }} />
  );
  const side: [string, string][] = [
    ["SCIENCE", "New telescope images reveal a faint ring of gas around a young star"],
    ["CITY", "Riverside park reopens after a winter of careful repairs"],
    ["CULTURE", "Small museums add late opening hours on weekends"],
    ["WEATHER", "Clear skies and mild winds expected through the weekend"],
  ];
  return (
    <Page bg="#FAF8F3" font={FONT.inter} color={ink}>
      <Abs style={{ left: 64 * u, top: 34 * u, fontSize: 16 * u, color: "#555" }}>Morning edition</Abs>
      <Abs style={{ right: 64 * u, top: 30 * u, display: "flex", gap: 16 * u }}>
        <div style={{ fontSize: 16 * u, padding: `${8 * u}px ${18 * u}px`, border: `${1 * u}px solid ${ink}` }}>Sign in</div>
        <div style={{ fontSize: 16 * u, padding: `${8 * u}px ${18 * u}px`, background: ink, color: "white" }}>Subscribe</div>
      </Abs>
      <Abs style={{ left: 0, width: 1920 * u, top: 70 * u, textAlign: "center", fontFamily: FONT.playfair, fontSize: 84 * u, fontWeight: 700 }}>
        The Daily Meridian
      </Abs>
      {rule(186, 64, 1792, 3)}
      <Abs style={{ left: 0, width: 1920 * u, top: 202 * u, display: "flex", justifyContent: "center", gap: 54 * u, fontSize: 18 * u, fontWeight: 600, letterSpacing: 1 * u }}>
        {["World", "City", "Science", "Culture", "Travel", "Food", "Sport", "Weather", "Opinion"].map((t) => (
          <span key={t}>{t}</span>
        ))}
      </Abs>
      {rule(246)}
      {/* lead story */}
      <WebImg name="lakeside_dawn" pos="50% 52%" zoom={1.3} style={{ left: 64 * u, top: 280 * u, width: 1080 * u, height: 520 * u }} />
      <Abs style={{ left: 64 * u, top: 816 * u, fontSize: 15 * u, color: "#666" }}>The northern shore just after sunrise.</Abs>
      <Abs style={{ left: 64 * u, top: 856 * u, width: 1080 * u, fontFamily: FONT.playfair, fontSize: 58 * u, fontWeight: 700, lineHeight: 1.08 }}>
        Spring arrives early along the northern lakes
      </Abs>
      <Abs style={{ left: 64 * u, top: 1000 * u, width: 1000 * u, fontFamily: FONT.playfair, fontSize: 24 * u, color: "#333", lineHeight: 1.5 }}>
        Warmer nights have opened the ice weeks ahead of the usual calendar, and the first boats are already out.
      </Abs>
      {/* side column */}
      <Abs style={{ left: 1196 * u, top: 280 * u, width: 1 * u, height: 780 * u, background: "#CFCAC0" }} />
      <Abs style={{ left: 1240 * u, top: 276 * u, width: 616 * u }}>
        {side.map(([k, h], i) => (
          <div key={k} style={{ paddingBottom: 26 * u, marginBottom: 26 * u, borderBottom: i < side.length - 1 ? `${1 * u}px solid #CFCAC0` : "none" }}>
            <div style={{ fontSize: 14 * u, fontWeight: 700, letterSpacing: 2 * u, color: "#A23B2A" }}>{k}</div>
            <div style={{ fontFamily: FONT.playfair, fontSize: 30 * u, fontWeight: 600, lineHeight: 1.2, marginTop: 8 * u }}>{h}</div>
          </div>
        ))}
        <WebImg name="kloppenheim_06_puresky" pos="50% 30%" zoom={1.5} style={{ position: "relative", width: 616 * u, height: 170 * u }} />
      </Abs>
    </Page>
  );
};
