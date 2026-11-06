const Features = () => {
  return (
    <>
      <div>
        <div className="py-[25px] sm:py-[48px] md:py-[80px] paddingX lg:flex justify-between bg-white">
          <div className="w-full lg:w-[50%]">
            <div className="flex gap-2">
              <div className="w-[16px] aspect-square rounded-full bg-[rgb(0,178,235)]"></div>
              <div className="w-[16px] aspect-square rounded-full bg-[#E83A7A]"></div>
            </div>
            <p className="text-xs sm:text-MEDIUM font-normal uppercase text-darkblue mt-[8px] sm:mt-[15px]">Features</p>
            <p className="text-[16px] sm:text-MEDIUM md:text-MEDIUM_2 lg:text-MEDIUM_3 xl:text-LARGE font-SEMIBOLD text-[#232F50] mt-[8px] sm:mt-[15px]">Features that actually save you time and clicks</p>
            <div className="flex justify-between flex-wrap gap-y-8 mt-[30px]">
              <div className="w-full lg:w-[45%] max-md:flex justify-between items-center">
                <div className="max-md:w-[30%]">
                  <img alt="https://cdn.ksmart.lsgkerala.gov.in/ui/web-portal/assets/paperless-ed518b68.svg" className="w-[40px]" decoding="async" loading="lazy" src="/images/paperless-ed518b68-63217f71.svg" />
                  <p className="text-xs sm:text-MEDIUM lg:text-MEDIUM_2 font-SEMIBOLD text-[#232F50] mt-[8px] sm:mt-[12px] leading-normal">Paperless</p>
                </div>
                <p className="text-xs sm:text-sm max-md:w-[70%] lg:text-[16px] font-normal text-[#5C6E93] sm:mt-[12px]">The transition to a paperless office has reduced our environmental footprint and streamlined our document management processes.</p>
              </div>
              <div className="w-full lg:w-[45%] max-md:flex justify-between items-center">
                <div className="max-md:w-[30%]">
                  <img alt="https://cdn.ksmart.lsgkerala.gov.in/ui/web-portal/assets/gisEnabled-8ec00e6b.svg" className="w-[40px]" decoding="async" loading="lazy" src="/images/gisEnabled-8ec00e6b-324ede6f.svg" />
                  <p className="text-xs sm:text-MEDIUM lg:text-MEDIUM_2 font-SEMIBOLD text-[#232F50] mt-[8px] sm:mt-[12px] leading-normal">GIS Enabled</p>
                </div>
                <p className="text-xs sm:text-sm max-md:w-[70%] lg:text-[16px] font-normal text-[#5C6E93] sm:mt-[12px]">A computer system for capturing, storing, checking, and displaying data related to positions on Earth's surface.</p>
              </div>
              <div className="w-full lg:w-[45%] max-md:flex justify-between items-center">
                <div className="max-md:w-[30%]">
                  <img alt="https://cdn.ksmart.lsgkerala.gov.in/ui/web-portal/assets/secure-3bb70093.svg" className="w-[40px]" decoding="async" loading="lazy" src="/images/secure-3bb70093-6ae46413.svg" />
                  <p className="text-xs sm:text-MEDIUM lg:text-MEDIUM_2 font-SEMIBOLD text-[#232F50] mt-[8px] sm:mt-[12px] leading-normal">Secure</p>
                </div>
                <p className="text-xs sm:text-sm max-md:w-[70%] lg:text-[16px] font-normal text-[#5C6E93] sm:mt-[12px]">
                  {" Security is paramount in today's digital age, requiring robust measures to protect sensitive data and ensure the safety of online interactions."}
                </p>
              </div>
              <div className="w-full lg:w-[45%] max-md:flex justify-between items-center">
                <div className="max-md:w-[30%]">
                  <img alt="https://cdn.ksmart.lsgkerala.gov.in/ui/web-portal/assets/certificatePreview-a9b7911c.svg" className="w-[40px]" decoding="async" loading="lazy" src="/images/certificatePreview-a9b7911c-c175dfdd.svg" />
                  <p className="text-xs sm:text-MEDIUM lg:text-MEDIUM_2 font-SEMIBOLD text-[#232F50] mt-[8px] sm:mt-[12px] leading-normal">Certificate Preview</p>
                </div>
                <p className="text-xs sm:text-sm max-md:w-[70%] lg:text-[16px] font-normal text-[#5C6E93] sm:mt-[12px]">The certificate preview allows you to review and verify the accuracy of your credentials before they are officially issued.</p>
              </div>
            </div>
          </div>
          <div className="w-full lg:w-[45%] hidden lg:block">
            <div className="w-full h-full rounded-[14px] text-white flex flex-col justify-end p-[36px]" style={{ backgroundImage: "url(\"/images/Paperless_2-4559af1b.webp\")", backgroundSize: "cover", backgroundPosition: "center center", objectFit: "cover" }}>
              <p className="text-LARGE font-SEMIBOLD">
                {" Paperless"}
              </p>
              <p className="text-[16px] text-[#C5C5C5] font-normal my-[16px]">
                {" The transition to a paperless office has reduced our environmental footprint and streamlined our document management processes."}
              </p>
              <a href="https://ksmart.lsgkerala.gov.in/ui/web-portal/about-us/features">
                <p className="text-[16px] text-[#00B2EB] font-normal flex">
                  Read More
                  <p className="ms-[5px] font-manrope">
                    {">"}
                  </p>
                </p>
              </a>
              <div className="w-full flex justify-center">
                <button aria-label="Play video" className="w-[34px] bg-[#848383] h-[30px] text-white rounded-l-full">
                  <svg fill="none" height="30" viewBox="0 0 30 30" width="30" xmlns="http://www.w3.org/2000/svg">
                    <path d="M17.6475 9.88239L12.7063 14.8236L17.6475 19.7647" stroke="white" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.85294"></path>
                  </svg>
                </button>
                <button aria-label="Play video" className="w-[34px] h-[30px] bg-[#848383] text-white rounded-r-full ms-[-1px]">
                  <svg fill="none" height="30" viewBox="0 0 30 30" width="30" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12.5288 9.88239L17.47 14.8236L12.5288 19.7647" stroke="white" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.85294"></path>
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default Features;
