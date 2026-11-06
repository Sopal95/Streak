const getHomeData = async (
  metadata?: Record<string, unknown>,
  { common }: { common?: any } = {}
) => {
  void metadata;
  void common;
  return {
    "status": 200,
    "PageHead": {
      "title": "Ksmart- Delivering Digital happiness",
      "meta": [
        {
          "name": "viewport",
          "content": "width=device-width, initial-scale=1.0"
        }
      ],
      "links": [
        {
          "rel": "icon",
          "href": "https://cdn.ksmart.lsgkerala.gov.in/ui/web-portal/favicon.ico",
          "type": "image/svg+xml"
        }
      ]
    }
  };
};

export default getHomeData;
