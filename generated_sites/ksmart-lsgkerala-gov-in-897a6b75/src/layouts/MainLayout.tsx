import { WidgetPlaceholder } from "streak-forge/components";

const MainLayout = () => {
  return (
    <html lang="en" data-theme="light" style={{ colorScheme: "light", "--zsiqf-custom-bg-color": "#e82c78", "--zsiqf-custom-bg": "#e82c78", "--zsiqf-cw-bg-color": "#e82c78", "--zsiqf-dynamic-text-color": "var(--zsiqf-primary-color)", "--zsiqf-dynamic-border-color": "#e82c78" } as any}>
      <head>
        <WidgetPlaceholder id="PageHead" type="PageHead" />
      </head>
      <body className="chakra-ui-light">
        <div id="root">
          <div>
            <main>
              <div className="4xl:flex justify-center">
                <div className="bg-[#F1F6FF] 4xl:w-[70%] 5xl:w-[60%] font-manrope">
                  <WidgetPlaceholder id="Support" type="Support" />
                  <div>
                    <WidgetPlaceholder id="Feature" type="Feature" />
                    <WidgetPlaceholder id="Hero" type="Hero" />
                    <WidgetPlaceholder id="QuickServices" type="QuickServices" />
                    <WidgetPlaceholder id="Services" type="Services" />
                    <WidgetPlaceholder id="TheLeadership" type="TheLeadership" />
                    <WidgetPlaceholder id="NewsAndEvents" type="NewsAndEvents" />
                    <WidgetPlaceholder id="Features" type="Features" />
                    <WidgetPlaceholder id="Hero2" type="Hero2" />
                    <WidgetPlaceholder id="LocalBodies" type="LocalBodies" />
                  </div>
                  <WidgetPlaceholder id="Footer" type="Footer" />
                </div>
              </div>
            </main>
          </div>
        </div>
      </body>
    </html>
  );
};

export default MainLayout;
