type PageHeadProps = {
  data?: {
    title?: string;
    meta?: Record<string, any>[];
    links?: Record<string, any>[];
  };
};

const PageHead = (props: PageHeadProps) => {
  const title = props?.data?.title ?? "";
  const meta = props?.data?.meta ?? [];
  const links = props?.data?.links ?? [];
  return (
    <>
      <meta charSet="UTF-8" />
      <title>{title}</title>
      {meta.map((m, i) => (
        <meta key={i} {...m} />
      ))}
      {links.map((l, i) => (
        <link key={i} {...l} />
      ))}
      <link rel="stylesheet" href="/styles/site.css" />
      <link rel="stylesheet" href="/styles/tailwind.css" />
    </>
  );
};

export default PageHead;
