import { useEffect, useState } from "react";
import "./Auth.css";
import StepIndicator from "../components/StepIndicator";
import { useNavigate } from "react-router-dom";

type LanguagePair = { language: string; level: string };
type RestCountryLang = { languages?: Record<string, string> };
type SignUpErrors = Partial<Record<string, string>>;
type RestCountry = { name: { common: string }; cca2: string };
type SignUpData = {
  firstName: string;
  lastName: string;
  email: string;
  yearOfBirth: string;
  gender: string;
  country: string;
  city: string;
  education: string;
  profession: string;
  languageRelated: string;
  nativeLanguage: string;
  languagePairs: LanguagePair[];
  password: string;
  confirmPassword: string;
  system: string;
  micType: string;
};

const initialSignUpData: SignUpData = {
  firstName: "",
  lastName: "",
  email: "",
  yearOfBirth: "",
  gender: "",
  country: "",
  city: "",
  education: "",
  profession: "",
  languageRelated: "",
  nativeLanguage: "",

  languagePairs: [
    { language: "", level: "" },
    { language: "", level: "" },
    { language: "", level: "" },
  ],

  password: "",
  confirmPassword: "",
  system: "",
  micType: "",
};




type SignInErrors = Partial<Record<"email" | "password", string>>;



function App() {
  const [signInData, setSignInData] = useState({ email: "", password: "" });
  const [signInErrors, setSignInErrors] = useState<SignInErrors>({});
  const [errors, setErrors] = useState<SignUpErrors>({});
  const [showSignUpPassword, setShowSignUpPassword] = useState(false);
  const [showSignUpConfirmPassword, setShowSignUpConfirmPassword] = useState(false);
  const navigate = useNavigate();
  const [languages, setLanguages] = useState<string[]>([]);
  const [loadingLanguages, setLoadingLanguages] = useState(false);
  const [countries, setCountries] = useState<string[]>([]);
  const [loadingCountries, setLoadingCountries] = useState(false);
  const [cities, setCities] = useState<string[]>([]);
  const [loadingCities, setLoadingCities] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState('signin')
  const [showPassword, setShowPassword] = useState(false)
  const [rememberMe, setRememberMe] = useState(false)
  const [signUpStep, setSignUpStep] = useState(1);
  const [signUpCompleted, setSignUpCompleted] = useState(false);
  const [showLangDropdown, setShowLangDropdown] = useState(false);
  const [signUpData, setSignUpData] = useState<SignUpData>(initialSignUpData);





            const levels = ["A1", "A2", "B1", "B2", "C1", "C2"];

            const updatePair = (index: number, key: "language" | "level", value: string) => {
              setSignUpData((prev) => {
                const next = [...prev.languagePairs];
                next[index] = { ...next[index], [key]: value };
                return { ...prev, languagePairs: next };
              });
            };

            const usedLanguages = signUpData.languagePairs.map((p) => p.language).filter(Boolean);

              
              

              function validateSignIn(): SignInErrors {
              const e: SignInErrors = {};

              if (!signInData.email.trim()) e.email = "Email is required";
              if (!signInData.password.trim()) e.password = "Password is required";

              return e;
            }

            




              const validateStep1 = (): SignUpErrors => {
              const e: SignUpErrors = {};

              if (!signUpData.firstName?.trim()) e.firstName = "First name is required";
              if (!signUpData.lastName?.trim()) e.lastName = "Last name is required";

              if (!signUpData.email?.trim()) e.email = "Email is required";
              else if (!/^\S+@\S+\.\S+$/.test(signUpData.email)) e.email = "Invalid email";

              if (!signUpData.yearOfBirth) e.yearOfBirth = "Year of birth is required";
              if (!signUpData.gender) e.gender = "Gender is required";

              if (!signUpData.country) e.country = "Country is required";
              if (!signUpData.city) e.city = "City is required";

              return e;
            };

            const validateStep2 = (): SignUpErrors => {
              const e: SignUpErrors = {};

              if (!signUpData.education) e.education = "Education is required";
              if (!signUpData.profession?.trim()) e.profession = "Profession is required";
              if (!signUpData.languageRelated) e.languageRelated = "Language Related is required";

              if (!signUpData.nativeLanguage) e.nativeLanguage = "Native language is required";

              
              signUpData.languagePairs.forEach((p, idx) => {
                if (!p.language) e[`languagePairs.${idx}.language`] = `Language ${idx + 1} is required`;
                if (!p.level) e[`languagePairs.${idx}.level`] = `Level ${idx + 1} is required`;
              });

              if (!signUpData.system) e.system = "System is required";
              if (!signUpData.micType) e.micType = "Mic type is required";

              return e;
            };
               


            const validateStep3 = (): SignUpErrors => {
              const e: SignUpErrors = {};

              if (!signUpData.password) e.password = "Password is required";
              else if (signUpData.password.length < 8) e.password = "Min 8 characters";

              if (!signUpData.confirmPassword) e.confirmPassword = "Confirm password is required";
              else if (signUpData.confirmPassword !== signUpData.password)
                e.confirmPassword = "Passwords do not match";

              return e;
            };

            const validateCurrentStep = (step: number): SignUpErrors => {
              if (step === 1) return validateStep1();
              if (step === 2) return validateStep2();
              return validateStep3();
            };


         

     


          const getPasswordStrength = (pw: string) => {
            if (!pw) return { level: 0, label: "", color: "" };

            let score = 0;
            if (pw.length >= 8) score++;
            if (/[A-Z]/.test(pw)) score++;
            if (/[0-9]/.test(pw)) score++;
            if (/[^A-Za-z0-9]/.test(pw)) score++;

            if (score <= 1) return { level: 1, label: "Weak", color: "red" };
            if (score === 2) return { level: 2, label: "Medium", color: "yellow" };
            return { level: 3, label: "Strong", color: "green" };
          };

                const strength = getPasswordStrength(signUpData.password);
                const [countryCodeByName, setCountryCodeByName] = useState<Record<string, string>>({});



                useEffect(() => {
                  if (signUpData.nativeLanguage) setShowLangDropdown(true);
                }, [signUpData.nativeLanguage]);


                

                              useEffect(() => {
                            if (activeTab === "signin") {
                              setSignUpStep(1);
                              setSignUpCompleted(false);
                              setSignUpData(initialSignUpData);
                              setShowLangDropdown(false);
                            }
                          }, [activeTab]);





                                useEffect(() => {
                    setLoadingCountries(true);

                    fetch("https://restcountries.com/v3.1/all?fields=name,cca2")
                      .then((res) => res.json() as Promise<RestCountry[]>)
                      .then((data) => {
                        const names = data
                          .map((c: RestCountry) => c.name.common)
                          .filter((x: string) => Boolean(x))
                          .sort((a: string, b: string) => a.localeCompare(b));

                        const map: Record<string, string> = {};
                        data.forEach((c: RestCountry) => {
                          if (c?.name?.common && c?.cca2) {
                            map[c.name.common] = c.cca2;
                          }
                        });

                        setCountries(names);
                        setCountryCodeByName(map);
                      })
                      .catch(() => {
                        setCountries([]);
                        setCountryCodeByName({});
                      })
                      .finally(() => setLoadingCountries(false));
                  }, []);




                useEffect(() => {
                  if (!signUpData.country) {
                    setCities([]);
                    return;
                  }

                  const iso2 = countryCodeByName[signUpData.country];
                  if (!iso2) {
                    setCities([]);
                    return;
                  }

                  const username = import.meta.env.VITE_GEONAMES_USERNAME as string | undefined;
                  if (!username) {
                    console.log("Missing GeoNames username");
                    setCities([]);
                    return;
                  }

                  setLoadingCities(true);
                  setSignUpData(prev => ({ ...prev, city: "" }));

                  const url =
                    `https://secure.geonames.org/searchJSON?` +
                    `country=${encodeURIComponent(iso2)}` +
                    `&featureClass=P` +
                    `&featureCode=PPLC` +
                    `&featureCode=PPLA` +
                    `&featureCode=PPLA2` +
                    `&orderby=name` +
                    `&maxRows=30` +
                    `&username=${username}`;

                  fetch(url)
                    .then(res => res.json())
                    .then(data => {
                      const list = (data.geonames ?? []).map(
                        (c: { name: string }) => c.name
                      );
                      setCities(list);
                    })
                    .catch(() => setCities([]))
                    .finally(() => setLoadingCities(false));
                }, [signUpData.country, countryCodeByName]);



                          
                        useEffect(() => {
                          setLoadingLanguages(true);

                          fetch("https://restcountries.com/v3.1/all?fields=languages")
                            .then((res) => res.json() as Promise<RestCountryLang[]>)
                            .then((data) => {
                              const set = new Set<string>();

                              data.forEach((c) => {
                                if (!c.languages) return;
                                Object.values(c.languages).forEach((lang) => set.add(lang));
                              });

                              setLanguages(Array.from(set).sort((a, b) => a.localeCompare(b)));
                            })
                            .catch(() => setLanguages([]))
                            .finally(() => setLoadingLanguages(false));
                        }, []);

                        useEffect(() => {
                          if (activeTab === "signin") {
                            setSignUpStep(1);
                            setSignUpCompleted(false);
                          }
                        }, [activeTab]);


                        

  return (
    <div className="sign-in-container">
      <div className="background-image">
        <img src="/background.png" alt="Background" />
      </div>

      <div className="right-side">
      <div className={`form-container ${activeTab === "signup" ? "form-container--signup" : ""}`}>

          {/* Tabs */}
          <div className="tab-list">
            <button
              className={`tab-button ${activeTab === 'signin' ? 'active' : ''}`}
              onClick={() => setActiveTab('signin')}
            >
              Sign In
            </button>
            <button
              className={`tab-button ${activeTab === 'signup' ? 'active' : ''}`}
              onClick={() => setActiveTab('signup')}
            >
              Sign Up
            </button>
          </div>

          <div className={`card ${activeTab === "signup" ? "card--signup" : ""}`}>

            {activeTab === 'signin' ? (
              <>
                <div className="card-header">
                  <h2 className="card-title">Welcome Back</h2>
                  <p className="card-description">
                    Sign in to continue contributing your voice
                  </p>
                </div>

                
                <form
                    className="sign-in-form"
                    onSubmit={(e) => {
                      e.preventDefault();

                      const errs = validateSignIn();
                      setSignInErrors(errs);

                      if (Object.keys(errs).length > 0) return;

                      navigate("/projects", { replace: true });
                    }}
                  >

                  <div className="form-field">
                        <label className="form-label">Email</label>

                        <div className="input-container">
                          <div className="input-wrapper">
                            <img src="/email-icon.svg" alt="" className="input-icon" />
                            <input
                              type="email"
                              className="form-input with-icon"
                              placeholder="Enter Your Email"
                              value={signInData.email}
                              onChange={(e) => {
                                setSignInData((p) => ({ ...p, email: e.target.value }));
                                if (signInErrors.email) setSignInErrors((p) => ({ ...p, email: "" }));
                              }}
                            />
                          </div>
                        </div>

                        {signInErrors.email && <p className="form-error">{signInErrors.email}</p>}
                      </div>


                    <div className="form-field">
                          <label className="form-label">Password</label>

                          <div className="input-container">
                            <div className="input-wrapper">
                              <img src="/password-icon.svg" alt="" className="input-icon" />

                              <input
                                type={showPassword ? "text" : "password"}
                                className="form-input with-icon with-right-icon"
                                placeholder="Enter Your Password"
                                value={signInData.password}
                                onChange={(e) => {
                                  setSignInData((p) => ({ ...p, password: e.target.value }));
                                  if (signInErrors.password) setSignInErrors((p) => ({ ...p, password: "" }));
                                }}
                              />

                              <button
                                type="button"
                                onClick={() => setShowPassword(!showPassword)}
                                className="password-toggle"
                              >
                                <img src="/eye-icon.svg" alt="" />
                              </button>
                            </div>
                          </div>

                          {signInErrors.password && <p className="form-error">{signInErrors.password}</p>}
                        </div>



                  <div className="form-options">
                    <div className="checkbox-container">
                      <input
                        type="checkbox"
                        checked={rememberMe}
                        onChange={(e) => setRememberMe(e.target.checked)}
                      />
                      <label>Remember me</label>
                    </div>
                    <a href="#">Forgot password?</a>
                  </div>

                  <button type="submit" className="sign-in-button">
                    Sign In
                  </button>
                </form>
              </>
            ) : (
              <>
                <div className="card-header">
                  <h2 className="card-title">Create Account</h2>
                  <p className="card-description">Start your journey</p>
                </div>

                <StepIndicator currentStep={signUpStep} totalSteps={3} completed={signUpCompleted} />

                
                <form
                  className="sign-up-form"
                  onSubmit={(e) => {
                    e.preventDefault();
                    setSignUpCompleted(true);
                    setTimeout(() => {
                      navigate("/projects", { replace: true });
                    }, 150);
                  }}  
                >
                  {/* First Name and Last Name */}
                  {signUpStep === 1 && (
                   <>
                  <div className="form-row">
                    <div className="form-field">
                      <label className="form-label">First Name</label>
                      <div className="input-container">
                        <div className="input-wrapper">
                          <input 
                            type="text" 
                            placeholder="First" 
                            className="form-input"
                            value={signUpData.firstName}
                            onChange={(e) => setSignUpData({...signUpData, firstName: e.target.value})}
                          />
                        </div>
                      </div>
                      {errors.firstName && <p className="form-error">{errors.firstName}</p>}
                    </div>
                    <div className="form-field">
                      <label className="form-label">Last Name</label>
                      <div className="input-container">
                        <div className="input-wrapper">
                          <input 
                            type="text" 
                            placeholder="Last " 
                            className="form-input"
                            value={signUpData.lastName}
                            onChange={(e) => setSignUpData({...signUpData, lastName: e.target.value})}
                          />
                        </div>
                      </div>
                          {errors.lastName && <p className="form-error">{errors.lastName}</p>}
                    </div>
                  </div>

                  {/* Email Field */}
                  <div className="form-field">
                    <label className="form-label">Email</label>
                    <div className="input-container">
                      <div className="input-wrapper">
                        <img src="/email-icon.svg" alt="" className="input-icon" />
                        <input 
                          type="email" 
                          placeholder="Enter Your Email" 
                          className="form-input with-icon"
                          value={signUpData.email}
                          onChange={(e) => setSignUpData({...signUpData, email: e.target.value})}
                        />
                      </div>
                    </div>
                    {errors.email && <p className="form-error">{errors.email}</p>}
                  </div>

                <div className="form-row">

                        {/* Year of Birth */}
                        <div className="form-field">
                          <label className="form-label">Year of Birth</label>
                          <div className="input-container">
                            <div className="input-wrapper">
                              <select
                                className="form-input"
                                value={signUpData.yearOfBirth}
                                onChange={(e) =>
                                  setSignUpData({ ...signUpData, yearOfBirth: e.target.value })
                                }
                              >
                                <option value="">Year</option>
                                {Array.from({ length: 100 }, (_, i) => {
                                  const year = new Date().getFullYear() - i;
                                  return (
                                    <option key={year} value={year}>
                                      {year}
                                    </option>
                                  );
                                })}
                              </select>
                            </div>
                          </div>
                          {errors.yearOfBirth && <p className="form-error">{errors.yearOfBirth}</p>}
                        </div>

                        {/* Gender */}
                        <div className="form-field">
                          <label className="form-label">Gender</label>
                          <div className="input-container">
                            <div className="input-wrapper">
                              <select
                                className="form-input"
                                value={signUpData.gender}
                                onChange={(e) =>
                                  setSignUpData({ ...signUpData, gender: e.target.value })
                                }
                              >
                                <option value="">Gender</option>
                                <option value="female">Female</option>
                                <option value="male">Male</option>
                              </select>
                            </div>
                          </div>
                          {errors.gender && <p className="form-error">{errors.gender}</p>}
                        </div>

                      </div>

                  {/* Country and City */}
                  <div className="form-row">
                 <div className="form-field">
                  <label className="form-label">Country</label>

                  <div className="input-container">
                    <div className="input-wrapper select-wrapper">
                      <select
                        className="form-input form-select"
                        value={signUpData.country}
                        onChange={(e) => {
                        console.log("Selected country:", e.target.value);
                        console.log("countries length:", countries.length);
                        setSignUpData({ ...signUpData, country: e.target.value });
                      }}

                      >
                        <option value="">
                          {loadingCountries ? "Loading countries..." : "Select your country"}
                        </option>

                        {countries.map((country:string) => (
                          <option key={country} value={country}>
                            {country}
                          </option>
                        ))}
                      </select>

                      <svg
                        className="select-arrow"
                        width="16"
                        height="16"
                        viewBox="0 0 16 16"
                        fill="none"
                      >
                        <path
                          d="M4 6L8 10L12 6"
                          stroke="#717182"
                          strokeWidth="1.33"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                        />
                      </svg>
                    </div>
                  </div>
                  {errors.country && <p className="form-error">{errors.country}</p>}
                </div>


                    <div className="form-field">
                      <label className="form-label">City</label>
                      <div className="input-container">
                        <div className="input-wrapper select-wrapper">

                          <select
                            className="form-input form-select"
                            value={signUpData.city}
                            onChange={(e) => setSignUpData({ ...signUpData, city: e.target.value })}
                            disabled={!signUpData.country || loadingCities}
                            style={{ opacity: signUpData.country ? 1 : 0.5 }}
                          >
                            <option value="">
                              {!signUpData.country
                                ? "Select country first"
                                : loadingCities
                                ? "Loading cities..."
                                : "Select your city"}
                            </option>

                            {cities.map((ct) => (
                              <option key={ct} value={ct}>{ct}</option>
                            ))}
                          </select>


                          <svg className="select-arrow" width="16" height="16" viewBox="0 0 16 16" fill="none" style={{opacity: 0.5}}>
                            <path d="M4 6L8 10L12 6" stroke="#717182" strokeWidth="1.33" strokeLinecap="round" strokeLinejoin="round"/>
                          </svg>
                        </div>
                      </div>
                           {errors.city && <p className="form-error">{errors.city}</p>}
                    </div>
                    </div>
                
                      <button
                        type="button"
                        className="sign-in-button"
                        onClick={() => {
                          const e = validateCurrentStep(signUpStep);
                          setErrors(e);

                          if (Object.keys(e).length > 0) return;

                          setSignUpStep((s) => s + 1);
                        }}
                      >
                        Next
                      </button>

                    </>
                  )}

                  {signUpStep === 2 && (
                      <>
                        <div className="form-row three-cols">
                          {/* Education */}
                          <div className="form-field">
                            <label className="form-label">Education</label>
                            <div className="input-container">
                            <div className="input-wrapper">
                              <select
                                className="form-input"
                                value={signUpData.education}
                                onChange={(e) =>
                                  setSignUpData({ ...signUpData, education: e.target.value })
                                }
                              >
                                <option value="">Select</option>
                                <option value="secondary">Secondary</option>
                                <option value="graduate">Graduate</option>
                                <option value="post_graduate">Post Graduate</option>
                              </select>
                            </div>
                          </div>
                               {errors.education && <p className="form-error">{errors.education}</p>}
                          </div>

                          {/* Profession */}
                          <div className="form-field">
                            <label className="form-label">Profession</label>
                            <div className="input-wrapper">
                              <input
                                type="text"
                                className="form-input"
                                placeholder="Profession"
                                value={signUpData.profession}
                                onChange={(e) =>
                                  setSignUpData({ ...signUpData, profession: e.target.value })
                                }
                              />
                            </div>
                            {errors.profession && <p className="form-error">{errors.profession}</p>}
                          </div>

                          {/* Language Related */}
                          <div className="form-field">
                            <label className="form-label">Language Related</label>
                            <div className="input-wrapper">
                              <select
                                className="form-input"
                                value={signUpData.languageRelated}
                                onChange={(e) =>
                                  setSignUpData({ ...signUpData, languageRelated: e.target.value })
                                }
                              >
                                <option value="">Select</option>
                                <option value="yes">Yes</option>
                                <option value="no">No</option>
                              </select>
                            </div>
                            {errors.languageRelated && <p className="form-error">{errors.languageRelated}</p>}
                          </div>
                          
                        </div>

                        {/* Native Language */}
                              <div className="form-field">
                                <label className="form-label">Native Language</label>

                                <div className="input-container">
                                  <div className="input-wrapper">
                                    <select
                                      className="form-input form-select"
                                      value={signUpData.nativeLanguage}
                                      onChange={(e) => {
                                        const newNative = e.target.value;

                                        setSignUpData((prev) => ({
                                          ...prev,
                                          nativeLanguage: newNative,
                                          languagePairs: prev.languagePairs.map((p) =>
                                            p.language === newNative ? { language: "", level: "" } : p
                                          ),
                                        }));

                                        setShowLangDropdown(true);
                                      }}
                                    >
                                      <option value="">
                                        {loadingLanguages ? "Loading languages..." : "Select Language"}
                                      </option>

                                      {languages.map((lang) => (
                                        <option key={lang} value={lang}>
                                          {lang}
                                        </option>
                                      ))}
                                    </select>
                                  </div>
                                </div>

                                {errors.nativeLanguage && <p className="form-error">{errors.nativeLanguage}</p>}
                              </div>


                           
                         {showLangDropdown && (
                            <>
                              {/* Languages */}
                              <div className="form-row three-cols">
                                {signUpData.languagePairs.map((pair, idx) => (
                                  <div className="form-field" key={`lang-${idx}`}>
                                    <label className="form-label">{`Language ${idx + 1}`}</label>

                                    <div className="input-container">
                                      <div className="input-wrapper select-wrapper">
                                        <select
                                          className="form-input form-select"
                                          value={pair.language}
                                          onChange={(e) => updatePair(idx, "language", e.target.value)}
                                        >
                                          <option value="">Select language</option>

                                          {languages
                                            .filter((l) => l !== signUpData.nativeLanguage)
                                            .filter((l) => !usedLanguages.includes(l) || l === pair.language)
                                            .map((lang) => (
                                              <option key={lang} value={lang}>
                                                {lang}
                                              </option>
                                            ))}
                                        </select>

                                        <svg className="select-arrow" width="16" height="16" viewBox="0 0 16 16" fill="none">
                                          <path d="M4 6L8 10L12 6" stroke="#717182" strokeWidth="1.33" strokeLinecap="round" strokeLinejoin="round" />
                                        </svg>
                                      </div>
                                    </div>

                                    {errors[`languagePairs.${idx}.language`] && (
                                      <p className="form-error">{errors[`languagePairs.${idx}.language`]}</p>
                                    )}
                                  </div>
                                ))}
                              </div>

                              {/* Levels */}
                              <div className="form-row three-cols">
                                {signUpData.languagePairs.map((pair, idx) => (
                                  <div className="form-field" key={`level-${idx}`}>
                                    <label className="form-label">{`Level ${idx + 1}`}</label>

                                    <div className="input-container">
                                      <div className="input-wrapper select-wrapper">
                                        <select
                                          className="form-input form-select"
                                          value={pair.level}
                                          disabled={!pair.language}
                                          onChange={(e) => updatePair(idx, "level", e.target.value)}
                                        >
                                          <option value="">
                                            {pair.language ? "Select level" : "Select language first"}
                                          </option>

                                          {levels.map((lv) => (
                                            <option key={lv} value={lv}>
                                              {lv}
                                            </option>
                                          ))}
                                        </select>

                                        <svg className="select-arrow" width="16" height="16" viewBox="0 0 16 16" fill="none">
                                          <path d="M4 6L8 10L12 6" stroke="#717182" strokeWidth="1.33" strokeLinecap="round" strokeLinejoin="round" />
                                        </svg>
                                      </div>
                                    </div>

                                    {errors[`languagePairs.${idx}.level`] && (
                                      <p className="form-error">{errors[`languagePairs.${idx}.level`]}</p>
                                    )}
                                  </div>
                                ))}
                              </div>
                            </>
                          )}


                          <div className="form-row">
                            {/* System */}
                            <div className="form-field">
                              <label className="form-label">System</label>
                              <div className="input-container">
                                <div className="input-wrapper select-wrapper">
                                  <select
                                    className="form-input form-select"
                                    value={signUpData.system}
                                    onChange={(e) =>
                                      setSignUpData({ ...signUpData, system: e.target.value })
                                    }
                                  >
                                    <option value="">System</option>
                                    <option value="opt1">Computer</option>
                                    <option value="opt2">Mobile</option>
                                  </select>

                                  <svg className="select-arrow" width="16" height="16" viewBox="0 0 16 16">
                                    <path d="M4 6L8 10L12 6" stroke="#717182" strokeWidth="1.33" />
                                  </svg>
                                </div>
                              </div>
                              {errors.system && <p className="form-error">{errors.system}</p>}
                            </div>

                            {/* Mic type */}
                            <div className="form-field">
                              <label className="form-label">Mic type</label>
                              <div className="input-container">
                                <div className="input-wrapper select-wrapper">
                                  <select
                                    className="form-input form-select"
                                    value={signUpData.micType}
                                    onChange={(e) =>
                                      setSignUpData({ ...signUpData, micType: e.target.value })
                                    }
                                  >
                                    <option value="">Mic type</option>
                                    <option value="optA">Professional mic</option>
                                    <option value="optB">Normal mic</option>
                                  </select>

                                  <svg className="select-arrow" width="16" height="16" viewBox="0 0 16 16">
                                    <path d="M4 6L8 10L12 6" stroke="#717182" strokeWidth="1.33" />
                                  </svg>
                                </div>
                              </div>
                              {errors.micType && <p className="form-error">{errors.micType}</p>}
                            </div>
                          </div>

                      

                        <div className="form-row">
                          <button
                            type="button"
                            className="sign-in-button"
                            onClick={() => setSignUpStep(1)}
                          >
                            Previous
                          </button>

                          <button
                            type="button"
                            className="sign-in-button"
                            onClick={() => {
                              const e = validateCurrentStep(signUpStep);
                              setErrors(e);

                              if (Object.keys(e).length > 0) return;

                              setSignUpStep((s) => s + 1);
                            }}
                          >
                            Next
                          </button>

                        </div>
                      </>
                    )}

                  {signUpStep === 3 && (
                        <>
                          <div className="form-row form-row--column">
                            
                            {/* Password */}

                            
                            <div className="form-field">
                              <label className="form-label password-label">
                                  Password
                                  <span className="tooltip">
                                    <button type="button" className="tooltip-icon" aria-label="Password requirements">
                                      !
                                    </button>
                                    <span className="tooltip-content">
                                      At least 8 characters, include an uppercase letter, a number, and a symbol.
                                    </span>
                                  </span>
                                </label>

                              <div className="input-container">
                                <div className="input-wrapper">
                                  <img src="/password-icon.svg" className="input-icon" />

                                  <input
                                    type={showSignUpPassword ? "text" : "password"}
                                    className="form-input with-icon with-right-icon"
                                    placeholder="Enter password"
                                    value={signUpData.password}
                                    onChange={(e) =>
                                      setSignUpData({ ...signUpData, password: e.target.value })
                                    }
                                  />

                                  <button
                                    type="button"
                                    onClick={() => setShowSignUpPassword((v) => !v)}
                                    className="password-toggle"
                                  >
                                    <img src="/eye-icon.svg" />
                                  </button>
                                </div>
                              </div>
                            </div>

                            {signUpData.password && (
                                <div className={`password-strength ${strength.color}`}>
                                  <div className="strength-bars">
                                    {[1, 2, 3].map((i) => (
                                      <span
                                        key={i}
                                        className={`strength-bar ${strength.level >= i ? "active" : ""}`}
                                      />
                                    ))}
                                  </div>

                                  <span className="strength-label">
                                    {strength.label}
                                  </span>
                                </div>
                                

                              )}
                                {errors.password && <p className="form-error">{errors.password}</p>}
                           {/* Confirm Password */}
                            <div className="form-field">
                              <label className="form-label">Confirm Password</label>

                              <div className="input-container">
                                <div className="input-wrapper">
                                  <img src="/password-icon.svg" className="input-icon" />

                                  <input
                                    type={showSignUpConfirmPassword ? "text" : "password"}
                                    className="form-input with-icon with-right-icon"
                                    placeholder="Confirm password"
                                    value={signUpData.confirmPassword}
                                    onChange={(e) =>
                                      setSignUpData({ ...signUpData, confirmPassword: e.target.value })
                                    }
                                  />

                                  <button
                                    type="button"
                                    onClick={() => setShowSignUpConfirmPassword((v) => !v)}
                                    className="password-toggle"
                                  >
                                    <img src="/eye-icon.svg" />
                                  </button>
                                </div>
                              </div>

                              {/* Match / Not match indicator */}
                              {signUpData.confirmPassword && (
                                <div
                                  className={`password-strength ${
                                    signUpData.confirmPassword === signUpData.password ? "green" : "red"
                                  }`}
                                >
                                  <span className="strength-label">
                                    {signUpData.confirmPassword === signUpData.password
                                      ? "Passwords match"
                                      : "Passwords do not match"}
                                  </span>
                                </div>
                              )}

                              {/* Error message */}
                              {errors.confirmPassword && (
                                <p className="form-error">{errors.confirmPassword}</p>
                              )}
                            </div>

                          </div>

                          <div className="form-row">
                            
                            <button
                              type="button"
                              className="sign-in-button"
                              onClick={() => setSignUpStep(2)}
                            >
                              Previous
                            </button>


                            <button
                                type="button"
                                className="sign-in-button"
                                onClick={() => {
                                  const e = validateStep3();
                                  setErrors(e);

                                  if (Object.keys(e).length > 0) return;

                                  setSignUpCompleted(true);
                                  navigate("/projects", { replace: true });
                                }}
                              >
                                Submit
                              </button>

                            </div>

                            <button
                              type="button"
                              className="sign-in-button"
                              onClick={() => {
                                setActiveTab("signin");
                                setSignUpStep(1);
                              }}
                            >
                              Cancel
                            </button>
                          
                        </>
                      )}

                </form>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
