const Hero = () => {
  return (
    <>
      <div>
        <div>
          <div className="lg:p-[22px] relative">
            <img alt="https://cdn.ksmart.lsgkerala.gov.in/common/webpage/homecarousel/carousel_13.webp" className="w-full min-h-[150px] xl:h-[500px] 2xl:h-full 3xl:h-full hover:cursor-pointer" decoding="async" height="838" loading="lazy" src="/images/carousel_13-a82fbe5e.webp" width="2400" />
            <div className="w-[35px] md:w-[50px] m-[15px] md:m-[60px] absolute bottom-0 right-0 flex items-center justify-between">
              <button>
                <img alt="https://cdn.ksmart.lsgkerala.gov.in/ui/web-portal/assets/arrow-31dd6715.svg" className="max-sm:w-[10px]" decoding="async" loading="lazy" src="/images/arrow-31dd6715-0b57e003.svg" />
              </button>
              <button className="rotate-180">
                <img alt="https://cdn.ksmart.lsgkerala.gov.in/ui/web-portal/assets/arrow-31dd6715.svg" className="max-sm:w-[10px]" decoding="async" loading="lazy" src="/images/arrow-31dd6715-0b57e003.svg" />
              </button>
            </div>
          </div>
          <div className="w-full relative flex flex-col justify-center max-sm:my-[10px] max-lg:my-[30px] mb-[30px] lg:absolute items-center lg:mt-[-70px] max-sm:px-[20px] sm:px-[40px] md:px-[35px]">
            <form className="w-full max-w-[882px]" siq_id="autopick_ia3ob7agnh">
              <div className="bg-white border-[1px] border-[#D5E3FB] shadow-sm w-full max-w-[882px] rounded-full p-[12px] flex justify-between items-center">
                <img alt="https://cdn.ksmart.lsgkerala.gov.in/ui/web-portal/assets/search-b5557f3d.svg" className="w-[24px] ms-3" decoding="async" loading="lazy" src="/images/search-b5557f3d-8f86fc4a.svg" />
                <input className="w-full h-[24px] sm:h-[33px] md:h-[40px] lg:h-[50px] outline-none px-3 text-[#5C6E93] placeholder:text-[#5C6E93] text-[16px] md:text-[18px]" placeholder="Find a service" type="text" />
                <button className="w-[70px] sm:w-[90px] xl:w-[120px] h-[33px] sm:h-[40px] lg:h-[50px] bg-primarypink border-[1px] border-primarypink rounded-full text-white text-xs sm:text-sm xl:text-[16px] font-SEMIBOLD max-sm:hidden">Search</button>
              </div>
            </form>
            <div className="w-full bg-white p-[25px] max-w-[882px] mt-[8px] rounded-[20px] border-[1px] border-[#E3E3E3] hidden">fff</div>
          </div>
        </div>
        <div className="w-full justify-center gap-4 hidden md:flex items-center text-[#5C6E93] text-[16px] font-NORMAL mt-[15px] mb-[30px]">
          <p>Suggested:</p>
          <button className="px-[24px] py-[16px] text-[#232F50] rounded-full hover:bg-white hover:shadow-xl">Right to Information</button>
          <button className="px-[24px] py-[16px] text-[#232F50] rounded-full hover:bg-white hover:shadow-xl">
            {"Trade License "}
          </button>
          <button className="px-[24px] py-[16px] text-[#232F50] rounded-full hover:bg-white hover:shadow-xl">Death Registration</button>
        </div>
      </div>
    </>
  );
};

export default Hero;
