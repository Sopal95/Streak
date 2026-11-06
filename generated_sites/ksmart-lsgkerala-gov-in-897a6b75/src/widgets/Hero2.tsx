const Hero2 = () => {
  return (
    <>
      <div>
        <div className="mt-[27px] bg-white py-[25px] sm:py-[48px] md:py-[80px] paddingX lg:flex justify-between items-center">
          <div className="w-full lg:w-[55%]">
            <p className="text-NORMAL_2 sm:text-MEDIUM md:text-MEDIUM_2 xl:text-LARGE text-[#E83A7A] font-normal leading-normal mb-[10px]">Introducing</p>
            <p className="text-MEDIUM sm:text-MEDIUM_2 md:text-MEDIUM_3 lg:text-XL xl:text-[48px] text-[#232F50] font-bold leading-normal">KSMART & Know Your Land</p>
            <p className="text-MEDIUM sm:text-MEDIUM_2 md:text-MEDIUM_3 lg:text-XL xl:text-[48px] text-[#232F50] font-light leading-normal">Mobile App</p>
            <p className="mt-[20px] text-xs sm:text-sm md:text-[16px] lg:text-[16px]_2 font-normal text-[#5C6E93] leading-normal">Unlock the features of KSMART app, granting users seamless access to a variety of government services. Enhance your decision-making with the GIS app, providing intelligent guidance for location-based choices</p>
            <button aria-controls="menu-list-:rm:" aria-expanded="false" aria-haspopup="menu" className="chakra-menu__menu-button w-full max-w-[450px] css-1s4qzdx" id="menu-button-:rm:">
              <span className="css-xl71ch">
                <button className="px-[24px] w-full max-w-[450px] py-[19px] bg-white border-[1px] border-[#00B2EB] rounded-full text-[#00B2EB] text-xs sm:text-sm xl:text-[16px] font-SEMIBOLD mt-[25px] lg:mt-[35px] xl:mt-[48px]">Download Now</button>
              </span>
            </button>
            <div className="css-1nzcalj" style={{ visibility: "hidden", position: "absolute", minWidth: "max-content", inset: "0px auto auto 0px" }}>
              <div aria-orientation="vertical" className="chakra-menu__menu-list w-full max-w-[450px] text-xs xl:text-sm font-medium cursor-pointer css-1uorelz" id="menu-list-:rm:" role="menu" style={{ transformOrigin: "var(--popper-transform-origin)", opacity: "0", visibility: "hidden", transform: "scale(0.8) translateZ(0px)" }} tabIndex={-1}>
                <button className="chakra-menu__menuitem css-1f5f0x7" data-index="0" id="menu-list-:rm:-menuitem-:rn:" role="menuitem" tabIndex={-1} type="button">
                  <button className="text-[#09327B] text-[20px] md:text-[22px] px-[10px] py-[15px] text-start h-full w-full">KSMART - Local Self Governement</button>
                </button>
                <button className="chakra-menu__menuitem css-1f5f0x7" data-index="1" id="menu-list-:rm:-menuitem-:ro:" role="menuitem" tabIndex={-1} type="button">
                  <button className="text-[#09327B] text-[20px] md:text-[22px] px-[10px] py-[15px] text-start h-full w-full">KSMART - Know Your Land</button>
                </button>
              </div>
            </div>
            <div className="bg-white w-full max-w-[450px] rounded-full p-[12px] hidden justify-between items-center border-[1px] border-[#E6E6E6] mt-[20px] lg:mt-[40px]">
              <input className="w-full h-[24px] sm:h-[33px] md:h-[40px] outline-none px-3 text-[rgba(18, 17, 39, 0.50)] placeholder:text-[#5C6E93] max-sm:text-xs" placeholder="Enter Mobile Number....." type="text" />
              <button className="max-sm:px-[11px] w-[110px] xl:w-[170px] h-[33px] sm:h-[40px] bg-[#00B2EB] border-[1px] border-[#00B2EB] rounded-full text-white text-xs sm:text-sm xl:text-[16px] font-SEMIBOLD">Get Link</button>
            </div>
            <img alt="mobile" className="w-full mt-[20px] lg:hidden" decoding="async" height="641" loading="lazy" src="/images/Phones-fb29f370.webp" width="744" />
            <div className="w-full flex justify-center lg:justify-start gap-4 mt-[20px] lg:mt-[40px]">
              <a href="https://play.google.com/store/apps/developer?id=Information+Kerala+Mission+Society" rel="noreferrer" target="_blank">
                <img alt="https://cdn.ksmart.lsgkerala.gov.in/ui/web-portal/assets/google_play-3853d920.png" className="h-[40px] lg:h-[60px] xl:h-[70px]" decoding="async" height="162" loading="lazy" src="/images/google_play-3853d920-aae83bb6.png" width="512" />
              </a>
              <a href="https://apps.apple.com/in/developer/information-kerala-mission/id1721293779" rel="noreferrer" target="_blank">
                {" "}
                <img alt="https://cdn.ksmart.lsgkerala.gov.in/ui/web-portal/assets/apple_store-43c9954b.png" className="h-[40px] lg:h-[60px] xl:h-[70px]" decoding="async" height="237" loading="lazy" src="/images/apple_store-43c9954b-c81d8acd.png" width="800" />
              </a>
              {" "}
            </div>
          </div>
          <img alt="app" className="w-[50%] max-lg:hidden" decoding="async" height="641" loading="lazy" src="/images/Phones-fb29f370.webp" width="744" />
        </div>
      </div>
    </>
  );
};

export default Hero2;
