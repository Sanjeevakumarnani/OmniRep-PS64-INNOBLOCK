export function asBytes32(value: unknown): string {
  if (typeof value !== 'string') {
    throw new Error('bytes32 value must be a string');
  }

  const hex = value.startsWith('0x') ? value : `0x${value}`;
  if (!/^0x[0-9a-fA-F]{64}$/.test(hex)) {
    throw new Error('Invalid bytes32: expected 32-byte hex value');
  }

  return hex;
}

export function asHexBytes(value: unknown): string {
  if (typeof value !== 'string') {
    throw new Error('signature value must be a string');
  }

  const hex = value.startsWith('0x') ? value : `0x${value}`;
  if (!/^0x(?:[0-9a-fA-F]{2})+$/.test(hex)) {
    throw new Error('Invalid signature: expected an even-length hex value');
  }

  return hex;
}
