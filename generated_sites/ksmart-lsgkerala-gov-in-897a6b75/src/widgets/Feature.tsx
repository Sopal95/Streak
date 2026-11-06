const Feature = () => {
  return (
    <>
      <div className="bg-[#232F50] p-[15px] flex items-center justify-center gap-[15px]">
        <img alt="info" decoding="async" loading="lazy" src="/images/info-bd1457d3-a3bbf335.svg" />
        <div className="w-[90%] md:w-[80%]">
          <div className="rfm-marquee-container" style={{ "--pause-on-hover": "running", "--pause-on-click": "paused", "--width": "100%", "--transform": "none" } as any}>
            <div className="rfm-marquee" style={{ "--play": "running", "--direction": "normal", "--duration": "24.9s", "--delay": "0s", "--iteration-count": "infinite", "--min-width": "100%" } as any}>
              <div className="rfm-initial-child-container">
                <div className="rfm-child" style={{ "--transform": "none" } as any}>
                  <p className="text-white font-medium text-[14px] sm:text-[20px] flex">കെട്ടിട നിര്‍മ്മാണ അനുമതി ലൈസന്‍സികള്‍ക്കായുള്ള ഓണ്‍ലൈന്‍ ക്ലാസുകള്‍ എല്ലാ പ്രവൃത്തി ദിവസങ്ങളിലും വൈകിട്ട് 4.00 മുതല്‍ 6.00 മണിവരെ നടത്തപ്പെടുന്നു.</p>
                </div>
              </div>
            </div>
            <div className="rfm-marquee" style={{ "--play": "running", "--direction": "normal", "--duration": "24.9s", "--delay": "0s", "--iteration-count": "infinite", "--min-width": "100%" } as any}>
              <div className="rfm-child" style={{ "--transform": "none" } as any}>
                <p className="text-white font-medium text-[14px] sm:text-[20px] flex">കെട്ടിട നിര്‍മ്മാണ അനുമതി ലൈസന്‍സികള്‍ക്കായുള്ള ഓണ്‍ലൈന്‍ ക്ലാസുകള്‍ എല്ലാ പ്രവൃത്തി ദിവസങ്ങളിലും വൈകിട്ട് 4.00 മുതല്‍ 6.00 മണിവരെ നടത്തപ്പെടുന്നു.</p>
              </div>
            </div>
          </div>
        </div>
        <button className="text-[#454545] text-[12px] sm:text-[16px] font-bold rounded-[8px] w-[80px] bg-[#E8ECEE] py-[7px] sm:py-[8px] decoration-[#00B2EB]">Join here</button>
      </div>
    </>
  );
};

export default Feature;
