import { Composition, Folder } from "remotion";
import { HelloWorld } from "./HelloWorld";
import { Logo } from "./HelloWorld/Logo";
import { Title } from "./HelloWorld/Title";
import { ZiyoCommercial } from "./ZiyoCommercial";
import { FPS, HEIGHT, SCENES, TOTAL_FRAMES, WIDTH } from "./timeline";
import { GENERIC_PAGES } from "./website/pages";
import { School } from "./website/sites/School";

// Each <Composition> is an entry in the sidebar!

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="ZiyoCommercial"
        component={ZiyoCommercial}
        durationInFrames={TOTAL_FRAMES}
        fps={FPS}
        width={WIDTH}
        height={HEIGHT}
      />

      {/* Scene 1 website pages: stills for the strip texture + the school page sequence (film frames). */}
      <Folder name="S01-Website">
        {GENERIC_PAGES.map((p) => (
          <Composition key={p.id} id={p.id} component={p.component} durationInFrames={1} fps={FPS} width={WIDTH} height={HEIGHT} />
        ))}
        <Composition
          id="S01-SchoolSite"
          component={School}
          durationInFrames={SCENES[0].durationInFrames}
          fps={FPS}
          width={WIDTH}
          height={HEIGHT}
        />
      </Folder>

      {/* Untouched Remotion starter template, kept for reference only. */}
      <Folder name="RemotionStarter">
        <Composition
          id="Logo"
          component={Logo}
          durationInFrames={150}
          fps={30}
          width={1920}
          height={1080}
          defaultProps={{
            logoColor1: "#91EAE4",
            logoColor2: "#86A8E7",
          }}
        />
        <Composition
          id="Title"
          component={Title}
          durationInFrames={115}
          fps={30}
          width={1920}
          height={1080}
          defaultProps={{
            titleText: "Welcome to Remotion",
            titleColor: "#000000",
          }}
        />
        <Composition
          id="HelloWorld"
          component={HelloWorld}
          durationInFrames={150}
          fps={30}
          width={1920}
          height={1080}
          defaultProps={{
            titleText: "Welcome to Remotion",
            titleColor: "#000000",
          }}
        />
      </Folder>
    </>
  );
};
