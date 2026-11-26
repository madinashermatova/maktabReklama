import React from "react";
import { FONT } from "../fonts";
import { Abs, Page, useU, WebImg } from "../kit";

/** Invented travel site "Horizon Trails" — no people, no real brands. */
export const Travel: React.FC = () => {
  const u = useU();
  const ink = "#1D2A2E";
  const field = (label: string, value: string, w: number) => (
    <div style={{ width: w * u, paddingLeft: 34 * u, borderLeft: `${1 * u}px solid #E4DED4` }}>
      <div style={{ fontSize: 15 * u, letterSpacing: 1.5 * u, color: "#8A8378", fontWeight: 600 }}>{label}</div>
      <div style={{ fontSize: 22 * u, marginTop: 6 * u, color: ink, fontWeight: 500 }}>{value}</div>
    </div>
  );
  const card = (img: Parameters<typeof WebImg>[0]["name"], pos: string, title: string, meta: string, x: number) => (
    <Abs style={{ left: x * u, top: 900 * u, width: 588 * u, height: 300 * u }}>
      <WebImg name={img} pos={pos} zoom={1.4} style={{ inset: 0, borderRadius: 22 * u }} />
      <Abs
        style={{
          left: 24 * u,
          bottom: 130 * u,
          background: "rgba(255,255,255,0.92)",
          borderRadius: 40 * u,
          padding: `${8 * u}px ${18 * u}px`,
          fontSize: 16 * u,
          fontWeight: 600,
          color: ink,
        }}
      >
        {meta}
      </Abs>
      <Abs style={{ left: 0, top: -54 * u, fontFamily: FONT.playfair, fontSize: 30 * u, color: ink }}>{title}</Abs>
    </Abs>
  );
  return (
    <Page bg="#F6F3EE" font={FONT.inter} color={ink}>
      {/* header */}
      <Abs style={{ left: 64 * u, top: 30 * u, fontFamily: FONT.playfair, fontSize: 36 * u, fontWeight: 600, fontStyle: "italic" }}>
        Horizon Trails
      </Abs>
      <Abs style={{ left: 560 * u, top: 40 * u, display: "flex", gap: 52 * u, fontSize: 19 * u, fontWeight: 500 }}>
        {["Destinations", "Journeys", "Stays", "Journal", "About"].map((t) => (
          <span key={t}>{t}</span>
        ))}
      </Abs>
      <Abs
        style={{
          right: 64 * u,
          top: 26 * u,
          padding: `${14 * u}px ${30 * u}px`,
          borderRadius: 40 * u,
          background: ink,
          color: "#F6F3EE",
          fontSize: 18 * u,
          fontWeight: 600,
        }}
      >
        Plan a trip
      </Abs>
      {/* hero */}
      <WebImg name="alps_field" pos="50% 42%" zoom={1.25} style={{ left: 48 * u, top: 104 * u, width: 1824 * u, height: 600 * u, borderRadius: 32 * u }} />
      <Abs
        style={{
          left: 48 * u,
          top: 104 * u,
          width: 1824 * u,
          height: 600 * u,
          borderRadius: 32 * u,
          background: "linear-gradient(180deg, rgba(10,20,30,0) 30%, rgba(10,20,30,0.55) 100%)",
        }}
      />
      <Abs style={{ left: 130 * u, top: 360 * u, color: "white", width: 1100 * u }}>
        <div style={{ fontSize: 18 * u, letterSpacing: 4 * u, fontWeight: 600, opacity: 0.9 }}>SPRING COLLECTION</div>
        <div style={{ fontFamily: FONT.playfair, fontSize: 92 * u, lineHeight: 1.02, marginTop: 14 * u }}>
          Find your next quiet place
        </div>
        <div style={{ fontSize: 24 * u, marginTop: 20 * u, opacity: 0.92 }}>
          Hand-picked mountain lodges, lake houses and open roads.
        </div>
      </Abs>
      {/* search bar */}
      <Abs
        style={{
          left: 200 * u,
          top: 650 * u,
          width: 1520 * u,
          height: 112 * u,
          borderRadius: 60 * u,
          background: "white",
          boxShadow: `0 ${18 * u}px ${50 * u}px rgba(30,40,50,0.18)`,
          display: "flex",
          alignItems: "center",
          paddingLeft: 22 * u,
        }}
      >
        <div style={{ display: "flex", marginLeft: -34 * u, borderLeft: "none" }}>
          {field("WHERE TO", "Mountains, lakes, coast", 430)}
          {field("WHEN", "Any week in May", 340)}
          {field("TRAVELLERS", "Two adults", 300)}
        </div>
        <Abs
          style={{
            right: 20 * u,
            top: 18 * u,
            height: 76 * u,
            width: 260 * u,
            borderRadius: 40 * u,
            background: "#D9673B",
            color: "white",
            fontSize: 22 * u,
            fontWeight: 700,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          Search
        </Abs>
      </Abs>
      {/* section */}
      {card("lakeside_dawn", "52% 55%", "Lakeside cabins", "12 stays", 48)}
      {card("rural_asphalt_road", "50% 60%", "Open road loops", "8 routes", 666)}
      {card("kloppenheim_06_puresky", "50% 35%", "Above the clouds", "5 lodges", 1284)}
    </Page>
  );
};
