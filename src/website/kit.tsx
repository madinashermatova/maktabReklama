import React from "react";
import { AbsoluteFill, Img, staticFile, useVideoConfig } from "remotion";
import "./fonts";

/** Resolution-independent unit: 1 = one pixel of the 1920-wide design (CLAUDE.md: no hard-coded pixel sizes). */
export const useU = (): number => {
  const { width } = useVideoConfig();
  return width / 1920;
};

/** One website page = one 16:9 frame. */
export const Page: React.FC<{ bg: string; children: React.ReactNode; font: string; color?: string }> = ({
  bg,
  children,
  font,
  color = "#111",
}) => (
  <AbsoluteFill style={{ backgroundColor: bg, fontFamily: font, color, overflow: "hidden" }}>{children}</AbsoluteFill>
);

/** CC0 web image (assets/web_images, Poly Haven previews — see docs/assets-credits.md), cropped with object-fit. */
export const WebImg: React.FC<{
  name: "alps_field" | "lakeside_dawn" | "rural_asphalt_road" | "kloppenheim_06_puresky";
  style: React.CSSProperties;
  pos?: string;
  zoom?: number;
}> = ({ name, style, pos = "50% 50%", zoom = 1 }) => (
  <div style={{ overflow: "hidden", position: "absolute", ...style }}>
    <Img
      src={staticFile(`web_images/${name}.png`)}
      style={{
        width: "100%",
        height: "100%",
        objectFit: "cover",
        objectPosition: pos,
        transform: `scale(${zoom})`,
        transformOrigin: pos,
      }}
    />
  </div>
);

export const Abs: React.FC<{ style: React.CSSProperties; children?: React.ReactNode }> = ({ style, children }) => (
  <div style={{ position: "absolute", ...style }}>{children}</div>
);
