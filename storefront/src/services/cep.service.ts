export interface ZipCodeLookupResult {
  zip_code: string;
  street: string;
  district: string;
  city: string;
  state: string;
}

interface ViaCepResponse {
  cep?: string;
  logradouro?: string;
  bairro?: string;
  localidade?: string;
  uf?: string;
  erro?: boolean;
}

function normalizeZipCode(value: string): string {
  return value.replace(/\D/g, "").slice(0, 8);
}

export async function lookupAddressByZipCode(zipCode: string): Promise<ZipCodeLookupResult> {
  const normalizedZipCode = normalizeZipCode(zipCode);
  if (normalizedZipCode.length !== 8) {
    throw new Error("Informe um CEP com 8 digitos para buscar o endereco.");
  }

  const response = await fetch(`https://viacep.com.br/ws/${normalizedZipCode}/json/`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error("Nao foi possivel consultar o CEP agora.");
  }

  const data = (await response.json()) as ViaCepResponse;
  if (data.erro) {
    throw new Error("CEP nao encontrado.");
  }

  return {
    zip_code: normalizedZipCode,
    street: data.logradouro?.trim() ?? "",
    district: data.bairro?.trim() ?? "",
    city: data.localidade?.trim() ?? "",
    state: data.uf?.trim() ?? "",
  };
}
