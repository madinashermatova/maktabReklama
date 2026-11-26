import type React from "react";
import { Bank } from "./sites/Bank";
import { Fitness } from "./sites/Fitness";
import { News } from "./sites/News";
import { Portfolio } from "./sites/Portfolio";
import { Store } from "./sites/Store";
import { Travel } from "./sites/Travel";

/**
 * Order of the scene-1 website strip, top → bottom (blender/kit/textures/website_strip.png).
 * The school website is always LAST (index 6), rendered from the S01-SchoolSite composition at S01_BEATS.scrollStop.
 */
export const GENERIC_PAGES: { id: string; component: React.FC }[] = [
  { id: "S01-Web-1-Travel", component: Travel },
  { id: "S01-Web-2-Store", component: Store },
  { id: "S01-Web-3-News", component: News },
  { id: "S01-Web-4-Fitness", component: Fitness },
  { id: "S01-Web-5-Bank", component: Bank },
  { id: "S01-Web-6-Portfolio", component: Portfolio },
];
