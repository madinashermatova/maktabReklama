import React from "react";
import { FONT } from "../fonts";
import { Abs, Page, useU, WebImg } from "../kit";

/** Invented architecture studio portfolio "Atelier North" — big type, landscape tiles, no people. */
export const Portfolio: React.FC = () => {
  const u = useU();
  const cream = "#EDE6DA";
  const tile = (x: number, img: Parameters<typeof WebImg>[0]["name"], pos: string, no: string, title: string, kind: string) => (
    <Abs style={{ left: x * u, top: 640 * u, width: 576 * u }}>
      <WebImg name={img} pos={pos} zoom={1.5} style={{ position: "relative", width: 576 * u, height: 330 * u, borderRadius: 6 * u, filter: "saturate(0.85)" }} />
      <div style={{ display: "flex", justifyContent: "space-between", marginTop: 18 * u, fontSize: 20 * u }}>
        <span>
          <span style={{ color: "#8D8779", marginRight: 14 * u }}>{no}</span>
          {title}
        </span>
        <span style={{ color: "#8D8779" }}>{kind}</span>
      </div>
    </Abs>
  );
  return (
    <Page bg="#141414" font={FONT.grotesk} color={cream}>
      <Abs style={{ left: 64 * u, top: 44 * u, fontSize: 26 * u, fontWeight: 700, letterSpacing: 1 * u }}>Atelier North</Abs>
      <Abs style={{ right: 64 * u, top: 48 * u, display: "flex", gap: 52 * u, fontSize: 20 * u }}>
        {["Work", "Studio", "Process", "Journal", "Contact"].map((t) => (
          <span key={t}>{t}</span>
        ))}
      </Abs>
      <Abs style={{ left: 64 * u, top: 150 * u, width: 1600 * u, fontFamily: FONT.playfair, fontSize: 112 * u, lineHeight: 1.02, letterSpacing: -2 * u }}>
        Spaces shaped by light <span style={{ fontStyle: "italic", color: "#C9A66B" }}>and quiet</span> materials.
      </Abs>
      <Abs style={{ left: 64 * u, top: 560 * u, fontSize: 20 * u, color: "#8D8779", letterSpacing: 3 * u }}>SELECTED WORK</Abs>
      <Abs style={{ left: 64 * u, top: 596 * u, width: 1792 * u, height: 1 * u, background: "#3A3732" }} />
      {tile(64, "lakeside_dawn", "48% 50%", "01", "Lake House", "Residential")}
      {tile(672, "kloppenheim_06_puresky", "50% 40%", "02", "Gallery of Light", "Cultural")}
      {tile(1280, "alps_field", "55% 45%", "03", "Mountain Retreat", "Hospitality")}
    </Page>
  );
};
