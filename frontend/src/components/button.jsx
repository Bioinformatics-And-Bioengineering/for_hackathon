import * as React from "react";
import Stack from "@mui/material/Stack";
import Button from "@mui/material/Button";

export default function BasicButtons({ onClick }) {
  return (
    <Stack spacing={2} direction="row">
      {/* <Button variant="text">Text</Button> */}
      <Button variant="contained" onClick={onClick}>
        次へ
      </Button>
      {/* <Button variant="outlined">Outlined</Button> */}
    </Stack>
  );
}
