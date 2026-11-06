type PageHeadProps = {
  data?: {
    title?: string;
    description?: string;
  };
};

const PageHead = (props: PageHeadProps) => {
  const title = props?.data?.title ?? "Hello Streak";
  const description = props?.data?.description ?? "A Streak.js app";

  return (
    <>
      <meta charSet="utf-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1" />
      <title>{title}</title>
      <meta name="description" content={description} />
      <meta property="og:title" content={title} />
      <meta property="og:description" content={description} />

      {/*
        No Preload here - tailwind.css is a small, render-blocking stylesheet
        the browser already discovers immediately via the <link> below, so a
        preload hint buys nothing. The one Preload this app uses (the hero
        background image) lives in HelloBanner - the widget that actually
        owns that image, not the shared page head.
      */}
      <link rel="stylesheet" href="/styles/tailwind.css" />
      <link rel="icon" href="/images/streak-logo.svg" type="image/svg+xml" />
    </>
  );
};

export default PageHead;
