import * as React from "react";
import Box from "@mui/material/Box";
import InputLabel from "@mui/material/InputLabel";
import FormControl from "@mui/material/FormControl";
import NativeSelect from "@mui/material/NativeSelect";

export default function NativeSelectDemo({
  options,
  labelText,
  idProp,
  onChange,
}) {
  return (
    <Box sx={{ minWidth: 120 }}>
      <FormControl fullWidth>
        <InputLabel
          variant="standard"
          htmlFor="uncontrolled-native"
        ></InputLabel>
        <NativeSelect
          //defaultValue={30}
          onChange={onChange} // ★ 修正点4: onChangeプロパティを渡す
          inputProps={{
            name: "age",
            id: "uncontrolled-native",
          }}
        >
          {options.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </NativeSelect>
      </FormControl>
    </Box>
  );
}
