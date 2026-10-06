export async function meetsOmniRep(registry, passportId, minimum, maxAge=0){
  return registry.meets(passportId, minimum, maxAge);
}

// Example: const allowed = await meetsOmniRep(registry, passportId, 400, 30*24*60*60);
