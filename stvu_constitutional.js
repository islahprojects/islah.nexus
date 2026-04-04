// ISLAH CONSTITUTIONAL FRAMEWORK - JS LAYER
const CONSTANTS = {
    SIGMA_CEILING: 0.93,
    SIGMA_FLOOR: 0.07,
    UNITY_FLOOR: 0.05,
    AI_INFLUENCE_CAP: 0.06
};

function checkLaw(sigma, unity) {
    if (sigma > CONSTANTS.SIGMA_CEILING || sigma < CONSTANTS.SIGMA_FLOOR) return "REJECT: LAW II";
    if (unity < CONSTANTS.UNITY_FLOOR) return "REJECT: LAW VII";
    return "PERMIT";
}

console.log("Islah Nexus Logic Initialized. Walang Maiiwan.");
